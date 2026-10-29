"""FastAPI routes for the home Sankalpa display."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal
import os
import swisseph as swe
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from indic_transliteration import sanscript
from .calendar import calculate
from .locations import CITIES
from .speech import audio_service, text_formats, SCHEMES
from .family_wording import family_templates, transliterate_template

WEB_DIR=Path(__file__).resolve().parent/'web'
app=FastAPI(title='Smartha Yajurveda Sankalpa')
app.mount('/static',StaticFiles(directory=WEB_DIR),name='static')

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
    return HTMLResponse((WEB_DIR/'index.html').read_text(encoding='utf8'),
                        headers={'Cache-Control':'no-store'})
