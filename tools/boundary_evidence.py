"""Export source and app calendar labels for predeclared turnover cases."""
import csv
from datetime import datetime
import json
from zoneinfo import ZoneInfo
from sankalpa_display import calendar as app
from .collect_reference import PLAN, read_capture
from sankalpa_display.lunisolar import dt_jd
from .validate_reference import REPORTS


def export():
    plan=json.loads(PLAN.read_text())
    cases=[]
    for split in ('development','holdout'):
        path=REPORTS/(split+'.json')
        if path.exists():cases.extend(json.loads(path.read_text())['cases'])
    selected=[c for c in cases if c['purpose']!='2026 daily coverage' or (c['date'] in ('2026-03-18','2026-03-19','2026-03-20','2026-03-21'))]
    rows=[]
    for case in sorted(selected,key=lambda c:(c['city'],c['date'])):
        source=read_capture(case)['data'];loc=plan['cities'][case['city']];tz=ZoneInfo(loc['timezone'])
        rise=app.sunrise_for(datetime.fromisoformat(case['date']).date(),loc)
        current=app.calculate(rise,loc)
        rows.append({'city':case['city'],'date':case['date'],'purpose':case['purpose'],
                     'source_tithi':source['tithi']['name'],'source_tithi_number':source['tithi']['number'],
                     'source_month':source['amanta_month']['name']['en'],'source_is_adhika':source['amanta_month']['is_adhika'],
                     'source_samvatsara':source['regional_metadata']['year']['samvatsara'],'app_samvatsara':current['samvatsara'],
                     'source_ritu':source['solar_ingress']['rutu']['en'],'app_ritu':current['ritu'],
                     'source_ayana':source['solar_ingress']['ayana']['en'],'app_ayana':current['ayana'],
                     'source_sunrise':dt_jd(source['sunrise_jd']).astimezone(tz).isoformat(timespec='seconds'),
                     'app_sunrise':rise.isoformat(timespec='seconds'),
                     'source_year_conjunction':dt_jd(source['regional_metadata']['year']['new_year_jd']).astimezone(tz).isoformat(timespec='seconds'),
                     'app_selected_year_boundary':current['year_boundary']})
    if rows:
        target=REPORTS/'year-boundaries.csv'
        with target.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        print(target,len(rows),'source/app boundary rows')


if __name__=='__main__':export()
