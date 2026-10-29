"""Local Smartha Panchanga reader. Astronomy via pyswisseph (license review required)."""
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
import swisseph as swe
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path
import os
from locations import CITIES
from speech import audio_service, text_formats, SCHEMES
from indic_transliteration import sanscript
from sankalpa import recital_values
from family_wording import family_templates, family_values, transliterate_template, calendar_audio_text
from lunisolar import jd, dt_jd, longitude, phase, month_info, cycle_year, year_boundary, ritu
from lunisolar import sunrise_for as event_sunrise, new_moon_before

app = FastAPI(title='Smartha Yajurveda Sankalpa')
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

@app.get('/api/panchanga')
def panchanga(at: str|None=Query(default=None),city: str=Query(default='bellevue'),
              sunrise_mode: Literal['hindu','apparent']='hindu',
              ritu_mode: Literal['solar','lunar']='solar',
              year_mode: Literal['sunrise','conjunction']='conjunction'):
    location=CITIES.get(city)
    if location is None:
        raise HTTPException(status_code=422, detail='Unknown city; choose one from /api/locations')
    tz=ZoneInfo(location['timezone'])
    if at:
        try:
            moment=datetime.fromisoformat(at)
        except ValueError as exc:
            raise HTTPException(status_code=422,detail='at must be an ISO 8601 date/time') from exc
        if moment.tzinfo is None:moment=moment.replace(tzinfo=tz)
    else:moment=datetime.now(tz)
    if not 1900<=moment.astimezone(tz).year<=2100:
        raise HTTPException(status_code=422,detail='Supported date range: 1900–2100')
    try:
        return calculate(moment,location,sunrise_mode,ritu_mode,year_mode)
    except (ValueError, swe.Error) as exc:
        raise HTTPException(status_code=422,detail='Calculation unavailable for this location/date') from exc

@app.get('/api/locations')
def locations():
    return list(CITIES.values())

@app.get('/api/text-formats')
def formats():
    return {**text_formats(),'family_templates':family_templates(),
            'family_profile':{'scope':'United States','source':'User screenshot supplied October 29, 2026',
                              'opening_closing':'Existing Yajurveda opening and session closing, confirmed by user',
                              'teacher_review':'pending'}}

class AudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    script: Literal['roman', 'sanskrit', 'kannada']

class TemplateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    script: Literal['roman', 'sanskrit', 'kannada']

@app.post('/api/template-formats')
def template_formats(request: TemplateRequest):
    """Convert an editable template locally, without audio-service limits."""
    import re
    allowed={'sandhya_action','gotra','location','country','samvatsara','ayana','ritu',
             'masa','paksha','tithi','vara','nakshatra','yoga','karana',
             'family_masa','family_tithi','family_vara'}
    allowed.update('recital_'+key for key in ('samvatsara','ayana','ritu','masa','paksha',
                                            'tithi','vara','nakshatra','yoga','karana'))
    tokens=re.findall(r'\{(\w+)\}',request.text)
    remainder=re.sub(r'\{\w+\}','',request.text)
    if not request.text.strip() or '{' in remainder or '}' in remainder or set(tokens)-allowed:
        raise HTTPException(status_code=422,detail='Check the calendar placeholders; use the fields listed below the editor.')
    return {'templates':{script:transliterate_template(request.text,SCHEMES[request.script],scheme)
                         for script,scheme in SCHEMES.items()}}

@app.post('/api/audio', status_code=202)
def generate_audio(request: AudioRequest):
    try:
        if os.environ.get('VERCEL')=='1':
            return JSONResponse(audio_service.generate_inline(request.text,request.script),
                                headers={'Cache-Control':'no-store'})
        return audio_service.start(request.text, request.script)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

@app.get('/api/audio/{key}')
def audio_status(key: str):
    try:
        return audio_service.status(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Audio not found') from exc

@app.get('/api/audio/{key}/file')
def audio_file(key: str):
    try:
        status=audio_service.status(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Audio not found') from exc
    if status['state'] != 'ready':
        raise HTTPException(status_code=409, detail='Audio is not ready yet')
    return FileResponse(audio_service.cache / (key+'.wav'), media_type='audio/wav',
                        filename='sankalpa.wav', headers={'Cache-Control': 'private, max-age=31536000, immutable'})

@app.get('/',response_class=HTMLResponse)
def home():
    return HTMLResponse(Path(__file__).with_name('index.html').read_text(encoding='utf8'),
                        headers={'Cache-Control':'no-store'})
