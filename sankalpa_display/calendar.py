"""Daily Panchanga calculation and recital values, independent of web routes."""
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
import swisseph as swe
from .locations import CITIES
from .wording import recital_values
from .family_wording import family_values, calendar_audio_text
from .lunisolar import jd, dt_jd, longitude, phase, month_info, cycle_year, year_boundary, ritu
from .lunisolar import sunrise_for as event_sunrise, new_moon_before

TZ = ZoneInfo('America/Los_Angeles')
LAT, LON = 47.6101, -122.2015
SID = swe.SIDM_LAHIRI
swe.set_sid_mode(SID)
TITHI = ['Pratipada','Dvitiya','Tritiya','Chaturthi','Panchami','Shashthi','Saptami','Ashtami','Navami','Dashami','Ekadashi','Dvadashi','Trayodashi','Chaturdashi','Purnima']
NAK = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati']
YOGA = ['Vishkambha','Priti','Ayushman','Saubhagya','Shobhana','Atiganda','Sukarma','Dhriti','Shula','Ganda','Vriddhi','Dhruva','Vyaghata','Harshana','Vajra','Siddhi','Vyatipata','Variyana','Parigha','Shiva','Siddha','Sadhya','Shubha','Shukla','Brahma','Indra','Vaidhriti']
VARA = ['Ravivara','Somavara','Mangalavara','Budhavara','Guruvara','Shukravara','Shanivara']
MASA = ['Vaishakha','Jyeshtha','Ashadha','Shravana','Bhadrapada','Ashwina','Kartika','Margashirsha','Pausha','Magha','Phalguna','Chaitra']
KARANA = ['Bava','Balava','Kaulava','Taitila','Garaja','Vanija','Vishti']
SAMVATSARA = ['Prabhava','Vibhava','Shukla','Pramoduta','Prajotpatti','Angirasa','Shrimukha','Bhava','Yuva','Dhata','Ishvara','Bahudhanya','Pramathi','Vikrama','Vrisha','Chitrabhanu','Svabhanu','Tarana','Parthiva','Vyaya','Sarvajit','Sarvadhari','Virodhi','Vikriti','Khara','Nandana','Vijaya','Jaya','Manmatha','Durmukhi','Hevilambi','Vilambi','Vikari','Sharvari','Plava','Shubhakrit','Shobhakrit','Krodhi','Vishvavasu','Parabhava','Plavanga','Kilaka','Saumya','Sadharana','Virodhikrit','Paridhavi','Pramadi','Ananda','Rakshasa','Nala','Pingala','Kalayukti','Siddharthi','Raudra','Durmati','Dundubhi','Rudhirodgari','Raktakshi','Krodhana','Akshaya']

def fields(j):
    sun=longitude(j,swe.SUN,True); moon=longitude(j,swe.MOON,True)
    p=phase(j)
    n=int(p//12) # 0..29
    t=TITHI[n%15] if n<15 else ('Amavasya' if n==29 else TITHI[n%15])
    if n==14:t='Purnima'
    kidx=int(p//6)
    if kidx==0:kar='Kimstughna'
    elif kidx>=57:kar=['Shakuni','Chatushpada','Naga'][kidx-57]
    else:kar=KARANA[(kidx-1)%7]
    return dict(tithi=t,paksha='Shukla' if n<15 else 'Krishna',nakshatra=NAK[int(moon/(360/27))%27],yoga=YOGA[int(((sun+moon)%360)/(360/27))%27],karana=kar,
        tithi_index=n,nak_index=int(moon/(360/27))%27,yoga_index=int(((sun+moon)%360)/(360/27))%27,karana_index=kidx,
        moon=moon,sun=sun)

def next_change(j,kind,limit_days=3,tz=TZ):
    field={'tithi':'tithi_index','nakshatra':'nak_index','yoga':'yoga_index','karana':'karana_index'}[kind]
    orig=fields(j)[field]
    lo=j; step=1/24
    hi=lo+step
    while fields(hi)[field]==orig and hi<j+limit_days:
        lo=hi;hi+=step
    if fields(hi)[field]==orig:return None
    for _ in range(30):
        mid=(lo+hi)/2
        if fields(mid)[field]==orig:lo=mid
        else:hi=mid
    return dt_jd(hi).astimezone(tz).isoformat(timespec='seconds')

def sunrise_for(d,location=None,convention='hindu'):
    return event_sunrise(d,location or CITIES['bellevue'],convention)


def lunar_month(j):
    return month_info(j)['name']


def year_label(j,tz=TZ,location=None,sunrise_mode='hindu',year_mode='conjunction'):
    place=location or CITIES['bellevue']
    year=cycle_year(j,place,sunrise_mode,year_mode)
    return SAMVATSARA[(39+year-2026)%60]


def calculate(moment,location=None,sunrise_mode='hindu',ritu_mode='solar',year_mode='conjunction'):
    location=location or CITIES['bellevue']
    tz=ZoneInfo(location['timezone'])
    j=jd(moment)
    f=fields(j)
    today=moment.astimezone(tz).date()
    rise=sunrise_for(today,location,sunrise_mode)
    # Keep sunrise-day metadata separate from the selected local date's Vara.
    # DrikGanita's date board labels October 29 as Thursday before sunrise too.
    pday=today if moment.astimezone(tz)>=rise else today-timedelta(days=1)
    f['vara']=VARA[(today.weekday()+1)%7]
    f['sunrise']=rise.isoformat(timespec='microseconds')
    f['panchanga_date']=pday.isoformat()
    month=month_info(j)
    f['masa']=month['name']
    f['month_type']=month['kind']
    f['is_adhika']=month['kind']=='adhika'
    f['is_nija']=month['kind']=='nija'
    f['is_kshaya']=month['kind']=='kshaya'
    f['omitted_month']=month['omitted_month']
    prefix={'adhika':'Adhika ','nija':'Nija ','normal':'','kshaya':''}[month['kind']]
    f['masa_display']=prefix+month['name']
    if f['is_kshaya']:
        f['masa_display']+=' (Kshaya: '+month['omitted_month']+' omitted; review required)'
    f['lunar_month_start']=dt_jd(month['start']).astimezone(tz).isoformat(timespec='microseconds')
    f['lunar_month_end']=dt_jd(month['end']).astimezone(tz).isoformat(timespec='microseconds')
    f['solar_ingresses_in_month']=month['solar_ingresses']
    f['samvatsara']=year_label(j,location=location,sunrise_mode=sunrise_mode,year_mode=year_mode)
    f['year_boundary']=dt_jd(year_boundary(today.year,location,sunrise_mode,year_mode)).astimezone(tz).isoformat(timespec='microseconds')
    f['ritu']=ritu(j,month['name'],ritu_mode)
    f['conventions']={'month':'amanta','ayanamsa':'lahiri','sunrise':sunrise_mode,'ritu':ritu_mode,'year':year_mode,'ayana':'sidereal_makara_karka','vara':'local_civil_date'}
    f['review_required']=f['is_kshaya']
    f['warnings']=['Kshaya month detected. Confirm the combined/omitted-month recital with your Panchanga authority.'] if f['is_kshaya'] else []
    f['ayana']='Uttarayana' if 270<=f['sun'] or f['sun']<90 else 'Dakshinayana' # sidereal Makara/Karka rule
    for item in ('tithi','nakshatra','yoga','karana'):
        f[item+'_ends']=next_change(j,item,tz=tz)
    f['timestamp']=moment.astimezone(tz).isoformat(timespec='seconds')
    f['location']=location['city']; f['timezone']=location['timezone']
    f['city_id']=location['id']; f['country']=location['country']
    f['latitude']=location['latitude']; f['longitude']=location['longitude']
    f['recital']=recital_values(f)
    f['family_recital']=family_values(f)
    f['calendar_audio']=calendar_audio_text(f)
    for k in ('sun','moon','tithi_index','nak_index','yoga_index','karana_index'):f.pop(k,None)
    return f
