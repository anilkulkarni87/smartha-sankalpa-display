"""Lahiri Amanta calendar events from bracketed Swiss Ephemeris calculations.

All intervals are [start, end). Numerical roots are separate from the selected
sunrise, Ritu and civil lunar-year conventions. No website data is used at runtime.
"""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import floor
from zoneinfo import ZoneInfo
import swisseph as swe

MONTHS = ['Vaishakha','Jyeshtha','Ashadha','Shravana','Bhadrapada','Ashwina',
          'Kartika','Margashirsha','Pausha','Magha','Phalguna','Chaitra']
RITUS = ['Vasanta','Grishma','Varsha','Sharad','Hemanta','Shishira']
MEAN_NEW_MOON = 2451550.09765
SYNODIC_MONTH = 29.530588861


def jd(moment):
    if moment.tzinfo is None:
        raise ValueError('A timezone-aware date/time is required')
    moment = moment.astimezone(timezone.utc)
    return swe.julday(moment.year,moment.month,moment.day,
        moment.hour+moment.minute/60+moment.second/3600+moment.microsecond/3.6e9)


def dt_jd(value):
    y,m,d,h=swe.revjul(value)
    return datetime(y,m,d,tzinfo=timezone.utc)+timedelta(hours=h)


def longitude(value,body,sidereal=False):
    if sidereal:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags=swe.FLG_MOSEPH|(swe.FLG_SIDEREAL if sidereal else 0)
    return swe.calc_ut(value,body,flags)[0][0]%360


def phase(value):
    return (longitude(value,swe.MOON)-longitude(value,swe.SUN))%360


def bisect_zero(function,lo,hi):
    if not function(lo)<=0<=function(hi):
        raise ValueError('Astronomical event is not bracketed')
    for _ in range(48):
        mid=(lo+hi)/2
        if hi-lo<1e-9:
            break
        if function(mid)<0:lo=mid
        else:hi=mid
    return (lo+hi)/2


@lru_cache(maxsize=8192)
def conjunction(index):
    estimate=MEAN_NEW_MOON+index*SYNODIC_MONTH
    # The mean phase provides only a bracket. The returned event is a true
    # longitude conjunction, with the 360/0 wrap removed around this bracket.
    return bisect_zero(lambda t:(phase(t)+180)%360-180,estimate-3,estimate+3)


def lunation_at(value):
    index=floor((value-MEAN_NEW_MOON)/SYNODIC_MONTH)
    while value<conjunction(index):index-=1
    while value>=conjunction(index+1):index+=1
    return index


def new_moon_before(value):
    return conjunction(lunation_at(value))


@lru_cache(maxsize=8192)
def month_record(index):
    start,end=conjunction(index),conjunction(index+1)
    start_sign=int(longitude(start,swe.SUN,True)//30)
    end_sign=int(longitude(end,swe.SUN,True)//30)
    ingresses=(end_sign-start_sign)%12
    if ingresses not in (0,1,2):
        raise ValueError('Unexpected solar ingress count in a lunar month')
    previous_start=conjunction(index-1)
    previous_sign=int(longitude(previous_start,swe.SUN,True)//30)
    previous_adhika=previous_sign==start_sign
    kind='adhika' if ingresses==0 else 'kshaya' if ingresses==2 else 'nija' if previous_adhika else 'normal'
    return (start,end,MONTHS[start_sign],kind,ingresses,
            MONTHS[(start_sign+1)%12] if ingresses==2 else None)


def month_info(value):
    start,end,name,kind,count,omitted=month_record(lunation_at(value))
    return dict(name=name,kind=kind,start=start,end=end,solar_ingresses=count,omitted_month=omitted)


@lru_cache(maxsize=8192)
def _sunrise(day,latitude,longitude_,timezone_,convention):
    tz=ZoneInfo(timezone_)
    start=jd(datetime(day.year,day.month,day.day,tzinfo=tz))
    method=swe.CALC_RISE
    if convention=='hindu':method|=swe.BIT_HINDU_RISING
    elif convention!='apparent':raise ValueError('Unknown sunrise convention')
    status,values=swe.rise_trans(start,swe.SUN,method,(longitude_,latitude,0),flags=swe.FLG_MOSEPH)
    if status!=0:raise ValueError('No sunrise available for this location/date')
    result=dt_jd(values[0]).astimezone(tz)
    if result.date()!=day:raise ValueError('No sunrise within the selected local date')
    return result


def sunrise_for(day,location,convention='hindu'):
    return _sunrise(day,location['latitude'],location['longitude'],location['timezone'],convention)


@lru_cache(maxsize=512)
def chaitra_conjunction(year):
    # An Adhika Chaitra must not trigger the regular-Chaitra year turnover.
    first=jd(datetime(year,2,1,tzinfo=timezone.utc))
    last=jd(datetime(year,6,1,tzinfo=timezone.utc))
    index=lunation_at(first)
    candidates=[]
    while conjunction(index)<last:
        start,_,name,kind,_,_=month_record(index)
        if first<=start<last and name=='Chaitra' and kind not in ('adhika','kshaya'):
            candidates.append(start)
        index+=1
    if len(candidates)!=1:
        raise ValueError('Could not establish a unique regular-Chaitra year boundary')
    return candidates[0]


@lru_cache(maxsize=2048)
def _year_boundary(year,latitude,longitude_,timezone_,sunrise_convention,year_convention):
    new_moon=chaitra_conjunction(year)
    if year_convention=='conjunction':return new_moon
    if year_convention!='sunrise':raise ValueError('Unknown year convention')
    day=dt_jd(new_moon).astimezone(ZoneInfo(timezone_)).date()
    rise=_sunrise(day,latitude,longitude_,timezone_,sunrise_convention)
    if jd(rise)<new_moon:
        rise=_sunrise(day+timedelta(days=1),latitude,longitude_,timezone_,sunrise_convention)
    # Samvatsara must never advance before the regular-Chaitra conjunction.
    # A civil Ugadi festival rule can choose the conjunction date even when
    # Pratipada touches no sunrise; that is not a calendar-year boundary.
    return jd(rise)


def year_boundary(year,location,sunrise_convention='hindu',year_convention='conjunction'):
    return _year_boundary(year,location['latitude'],location['longitude'],location['timezone'],sunrise_convention,year_convention)


def cycle_year(value,location,sunrise_convention='hindu',year_convention='conjunction'):
    year=dt_jd(value).astimezone(ZoneInfo(location['timezone'])).year
    return year if value>=year_boundary(year,location,sunrise_convention,year_convention) else year-1


def ritu(value,month_name,convention='solar'):
    if convention=='solar':
        # Soura pairing: Mesha/Vrishabha, Mithuna/Karka, etc. An inserted
        # lunar month does not advance the sidereal Sun or the solar season.
        return RITUS[int(longitude(value,swe.SUN,True)//60)]
    if convention=='lunar':
        chaitra_order=['Chaitra']+MONTHS[:-1]
        return RITUS[chaitra_order.index(month_name)//2]
    raise ValueError('Unknown Ritu convention')
