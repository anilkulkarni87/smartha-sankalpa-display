"""Capture public DrikGanita calculations for offline comparison; never an oracle.

The POST endpoint is the website's read-only calculation request. No account,
credentials, push subscriptions or feedback endpoints are used. Responses are
cached with request provenance and a hash of the exact response bytes.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from sankalpa_display.locations import CITIES

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'validation'/'reference'
PLAN=REFERENCE/'plan.json'
ENDPOINT='https://drikganita.com/api/v1/panchang'
ENGINE_FILES=['app.py', *['sankalpa_display/'+name+'.py' for name in ('api','calendar','lunisolar','locations','wording','speech','family_wording')]]


def engine_hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ENGINE_FILES}


def make_plan():
    if PLAN.exists():return json.loads(PLAN.read_text())
    rows=[]
    for city in ('bellevue','bengaluru','sydney'):
        day=date(2026,1,1)
        while day.year==2026:
            text=day.isoformat()
            known=city=='bellevue' and (day.month==5 or text in ('2026-06-20','2026-10-28'))
            split='holdout' if not known and int(hashlib.sha256(f'drik-2026-v1:{city}:{text}'.encode()).hexdigest()[:8],16)%5==0 else 'development'
            rows.append({'city':city,'date':text,'split':split,'purpose':'2026 daily coverage'})
            day+=timedelta(days=1)
    # Predeclared boundary cases, not selected after seeing reference answers.
    # Sunrise multiplicity was found by our engine; expected labels come only
    # from DrikGanita. This tests observed cases, not all years 1900–2100.
    for city,center,purpose in [
        ('bengaluru','2037-03-17','repeated-Pratipada candidate'),
        ('bengaluru','2032-04-10','skipped-Pratipada candidate'),
        *[(city,'2029-03-16','Adhika Chaitra') for city in ('bellevue','bengaluru','sydney')],
        *[(city,'2029-04-14','regular Chaitra after Adhika') for city in ('bellevue','bengaluru','sydney')],
    ]:
        for offset in (-1,0,1,2):
            rows.append({'city':city,'date':(date.fromisoformat(center)+timedelta(days=offset)).isoformat(),'split':'development','purpose':purpose})
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),'source':ENDPOINT,
          'profile':{'region':'kannada','sunrise_type':'centre','altitude':0,'calc_method':'drik','kalam_basis':'sunrise','ekadashi_school':'smarta'},
          'cities':{city:CITIES[city] for city in ('bellevue','bengaluru','sydney')},
          'engine_before_capture':engine_hashes(),
          'split_rule':'sha256(drik-2026-v1:city:date) first 8 hex digits modulo 5 == 0; already inspected Bellevue May and two known dates excluded',
          'holdout_policy':'Do not evaluate reserved external answers until development changes are frozen. Final results cannot be used as a new unseen test after tuning.',
          'cases':rows}
    REFERENCE.mkdir(parents=True,exist_ok=True)
    PLAN.write_text(json.dumps(plan,indent=2)+'\n')
    return plan


def path_for(case):return REFERENCE/case['city']/(case['date']+'.json.gz')


def read_capture(case):
    with gzip.open(path_for(case),'rt',encoding='utf8') as f:return json.load(f)


def validate_capture(capture,case,plan):
    raw=capture['raw_response_utf8'].encode('utf8')
    metadata=capture['provenance'];data=capture['data'];loc=plan['cities'][case['city']]
    if metadata['endpoint']!=ENDPOINT:
        raise ValueError('Unexpected reference endpoint')
    if hashlib.sha256(raw).hexdigest()!=metadata['response_sha256'] or json.loads(raw)!=data:
        raise ValueError('Reference payload hash or parsed facts mismatch')
    expected={**plan['profile'],'date':case['date'],'time':'12:00',
              'lat':loc['latitude'],'lon':loc['longitude'],'timezone':loc['timezone']}
    if metadata['request']!=expected:
        raise ValueError('Reference request does not match predeclared case/profile')
    if (data.get('date'),data.get('timezone'),data.get('region'))!=(case['date'],loc['timezone'],'kannada'):
        raise ValueError('Reference response date/timezone/region mismatch')
    if data.get('calc_method')!='drik':
        raise ValueError('Reference effective calculation method is not Drik')
    position=data.get('location',{})
    if abs(position.get('lat',999)-loc['latitude'])>1e-5 or abs(position.get('lon',999)-loc['longitude'])>1e-5:
        raise ValueError('Reference response coordinates mismatch')


lock=threading.Lock()
next_request=0.0
request_gap=1.0
stop=threading.Event()


def fetch_case(case,plan,attempts=3,timeout_seconds=60):
    global next_request
    path=path_for(case)
    if path.exists():return 'cached'
    loc=plan['cities'][case['city']]
    params={**plan['profile'],'date':case['date'],'time':'12:00',
            'lat':loc['latitude'],'lon':loc['longitude'],'timezone':loc['timezone']}
    for attempt in range(attempts):
        if stop.is_set():raise RuntimeError('Collection stopped after an access/rate-limit response')
        with lock:
            delay=max(0,next_request-time.monotonic())
            next_request=max(time.monotonic(),next_request)+request_gap
        if delay:time.sleep(delay)
        req=Request(ENDPOINT,data=json.dumps(params).encode(),headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'SankalpaCalendarValidation/1.0 (public reference comparison)'})
        try:
            started=time.monotonic()
            with urlopen(req,timeout=timeout_seconds) as response:
                raw=response.read();headers={key:response.headers.get(key) for key in ('Date','ETag','Last-Modified','Content-Type')}
            data=json.loads(raw)
            if data.get('date')!=case['date'] or data.get('timezone')!=loc['timezone'] or data.get('region')!='kannada':
                raise ValueError('Reference response date/timezone/profile does not match request')
            source_location=data.get('location',{})
            if abs(source_location.get('lat',999)-loc['latitude'])>1e-5 or abs(source_location.get('lon',999)-loc['longitude'])>1e-5:
                raise ValueError('Reference response coordinates do not match request')
            capture={'provenance':{'endpoint':ENDPOINT,'method':'POST (read-only calculation)','request':params,
                     'captured_utc':datetime.now(timezone.utc).isoformat(),'headers':headers,
                     'response_sha256':hashlib.sha256(raw).hexdigest(),'elapsed_seconds':round(time.monotonic()-started,3)},
                     'data':data}
            path.parent.mkdir(exist_ok=True)
            # Keep the exact bytes as well as parsed facts, so hashing remains verifiable.
            capture['raw_response_utf8']=raw.decode('utf8')
            with gzip.open(path.with_suffix('.tmp'),'wt',encoding='utf8') as f:json.dump(capture,f,ensure_ascii=False,separators=(',',':'))
            path.with_suffix('.tmp').replace(path)
            return 'captured'
        except HTTPError as exc:
            if exc.code in (401,403,429):stop.set();raise
            if exc.code<500 or attempt==attempts-1:raise
        except (OSError,TimeoutError):
            if attempt==attempts-1:raise
        time.sleep(2**attempt)
    raise RuntimeError('Capture did not complete')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--workers',type=int,choices=range(1,9),default=2)
    parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--probe',action='store_true',help='Try only the first uncaptured case, once, with a 45-second timeout')
    args=parser.parse_args();plan=make_plan()
    if args.plan_only:
        print(json.dumps({'cases':len(plan['cases']),'holdout':sum(x['split']=='holdout' for x in plan['cases'])}));return
    # Check rare boundary cases early, then interleave cities by calendar date.
    ordered=sorted(plan['cases'],key=lambda c:(c['purpose']=='2026 daily coverage',c['date'],c['city']))
    cases=ordered[:args.limit] if args.limit else ordered
    if args.probe:
        cases=[case for case in ordered if not path_for(case).exists()][:1]
        if not cases:
            print('All predeclared cases are already captured');return
    failures=[];completed=0;consecutive_failures=0;started=time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(fetch_case,case,plan,1 if args.probe else 3,45 if args.probe else 60):case for case in cases}
        for job in as_completed(jobs):
            case=jobs[job]
            try:
                state=job.result()
                if state=='captured':consecutive_failures=0
            except Exception as exc:
                failures.append({'case':case,'error':f'{type(exc).__name__}: {exc}'})
                consecutive_failures+=1
                if consecutive_failures>=3:stop.set()
                print('FAILED',case['city'],case['date'],str(exc),flush=True)
                if stop.is_set():
                    for pending in jobs:pending.cancel()
                    break
            completed+=1
            if completed%10==0 or completed==len(cases):print(f'{completed}/{len(cases)} reference cases processed; {len(failures)} failures; elapsed {time.monotonic()-started:.0f}s',flush=True)
    status={'processed':completed,'requested':len(cases),'failures':failures,'captured_files':len(list(REFERENCE.glob('*/*.json.gz'))),'updated_utc':datetime.now(timezone.utc).isoformat()}
    (REFERENCE/'capture-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps(status),flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
