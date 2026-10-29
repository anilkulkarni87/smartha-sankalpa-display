"""Offline DrikGanita comparison with explicit coverage and reserved final cases.

No web calls occur here. Calendar answers come only from captured external facts;
app-generated values are never saved as expected answers. Minute board fixtures
remain separate. Source Julian days expose finer precision; the initial 60-second
agreement target is retained explicitly, not described as observational accuracy.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from zoneinfo import ZoneInfo
import app
from lunisolar import dt_jd, jd
from collect_reference import PLAN, REFERENCE, engine_hashes, path_for, read_capture, validate_capture

REPORTS=REFERENCE.parent/'reports'
TOLERANCE_SECONDS=60
ALIAS={
 'sarat':'sharad','karttika':'kartika','virodhikrt':'virodhikrit','harsana':'harshana','subha':'shubha','pausa':'pausha','vaidhrti':'vaidhriti','sukarman':'sukarma','dhrti':'dhriti',
 'pusya':'pushya','citra':'chitra','purvasadha':'purvaashadha','uttarasadha':'uttaraashadha',
 'trtiya':'tritiya','pancami':'panchami','sakuni':'shakuni','catuspada':'chatushpada',
 'vaisakha':'vaishakha','anuradha':'anuradha','vrddhi':'vriddhi','sadhya':'sadhya',
 'brahman':'brahma','siddha':'siddha','caitra':'chaitra','sobhakrt':'shobhakrit',
 'sisira':'shishira','hemanta':'hemanta','varsa':'varsha','sadharana':'sadharana',
 'caturthi':'chaturthi','caturdasi':'chaturdashi','sasthi':'shashthi',
 'sasti':'shashthi','astami':'ashtami','dasami':'dashami','ekadasi':'ekadashi',
 'dvadasi':'dvadashi','trayodasi':'trayodashi','asvini':'ashwini','aswini':'ashwini',
 'krttika':'krittika','mrgasira':'mrigashira','mrgasirsa':'mrigashira','mrigasira':'mrigashira',
 'aslesa':'ashlesha','visakha':'vishakha','jyestha':'jyeshtha','asadha':'ashadha',
 'sravana':'shravana','dhanistha':'dhanishtha','satabhisa':'shatabhisha',
 'viskambha':'vishkambha','ayusman':'ayushman','sobhana':'shobhana','sula':'shula',
 'variyaṇa':'variyana','variyan':'variyana','siva':'shiva','sukla':'shukla',
 'gara':'garaja','visti':'vishti','kaksaya':'kshaya','asvina':'ashwina',
 'margasirsa':'margashirsha','visvavasu':'vishvavasu','daksinayana':'dakshinayana',
 'grisma':'grishma','sarad':'sharad','svati':'swati','kimstughna':'kimstughna',
 'krsna':'krishna','krodhi':'krodhi',
}


def normalize(value):
    plain=''.join(c for c in unicodedata.normalize('NFKD',str(value)) if not unicodedata.combining(c))
    plain=re.sub('[^a-z]','',plain.lower())
    return ALIAS.get(plain,plain)


def month_name(value):
    return normalize(re.sub(r'^(Adhika|Nija|Shuddha)\s+','',value,flags=re.I))


def source_segment(data,field,value):
    sequence=data.get('day_sequence',{}).get({'tithi':'tithis','nakshatra':'nakshatras','yoga':'yogas','karana':'karanas'}[field],[])
    for segment in sequence:
        if segment['start_jd']<=value<segment['end_jd']:
            return segment
    return None


class Comparison:
    def __init__(self):
        self.counts=defaultdict(Counter);self.failures=[];self.uncertain=[];self.differences=defaultdict(list)

    def record(self,case,sample,field,actual,expected,*,seconds=False,uncertain=False,reason=None):
        key=case['city']+'/'+sample+'/'+field
        if reason:
            self.counts[key]['unavailable']+=1;return
        if uncertain:
            self.counts[key]['uncertain']+=1
            self.uncertain.append({'city':case['city'],'date':case['date'],'sample':sample,'field':field,
                                   'actual':actual,'reference':expected,'reason':'Within 60 seconds of a source transition or in a source interval gap'})
            return
        if seconds:
            delta=round(float(actual)-float(expected),6)
            self.differences[key].append(abs(delta));ok=abs(delta)<=TOLERANCE_SECONDS
        else:delta=None;ok=actual==expected
        self.counts[key]['passed' if ok else 'failed']+=1
        if not ok:self.failures.append({'city':case['city'],'date':case['date'],'purpose':case['purpose'],
                                        'sample':sample,'field':field,'actual':actual,'reference':expected,'difference_seconds':delta})

    def compare(self,case,capture,location):
        data=capture['data'];tz=ZoneInfo(location['timezone']);day=datetime.fromisoformat(case['date']).replace(tzinfo=tz)
        rise=app.sunrise_for(day.date(),location)
        # Source labels use the source's precise sunrise. Our sunrise differs
        # slightly; ambiguous labels near transitions are counted separately.
        for sample,moment in [('sunrise',rise+timedelta(seconds=.1)),('noon',day.replace(hour=12)),('evening',day.replace(hour=18))]:
            value=jd(moment);actual=app.calculate(moment,location)
            if sample=='sunrise':
                self.record(case,sample,'sunrise',jd(rise)*86400,data['sunrise_jd']*86400,seconds=True)
            for field in ('tithi','nakshatra','yoga','karana'):
                segment=data.get(field) if sample=='sunrise' else source_segment(data,field,value)
                if not segment:
                    self.record(case,sample,field,None,None,reason='Source sequence does not cover this instant');continue
                ambiguous=min(abs(value-segment['start_jd']),abs(value-segment['end_jd']))*86400<=TOLERANCE_SECONDS
                # At sunrise the day_sequence's start is clipped to sunrise;
                # top-level intervals preserve the true event start instead.
                self.record(case,sample,field,normalize(actual[field]),normalize(segment['name']),uncertain=ambiguous)
                self.record(case,sample,field+'_end',jd(datetime.fromisoformat(actual[field+'_ends']))*86400,segment['end_jd']*86400,seconds=True,uncertain=ambiguous)
                if field=='tithi':
                    number=segment['number']
                    self.record(case,sample,'paksha',normalize(actual['paksha']),'shukla' if number<=15 else 'krishna',uncertain=ambiguous)
            month=data['amanta_month']
            if month['start_jd']<=value<month['end_jd']:
                ambiguous=min(abs(value-month['start_jd']),abs(value-month['end_jd']))*86400<=TOLERANCE_SECONDS
                self.record(case,sample,'masa',normalize(actual['masa']),month_name(month['name']['en']),uncertain=ambiguous)
                self.record(case,sample,'is_adhika',actual['is_adhika'],month['is_adhika'],uncertain=ambiguous)
            else:
                for field in ('masa','is_adhika'):self.record(case,sample,field,None,None,reason='Conjunction crossed after source sunrise; next month not supplied')
            if sample=='sunrise':
                self.record(case,sample,'vara',actual['vara'],{'Sunday':'Ravivara','Monday':'Somavara','Tuesday':'Mangalavara','Wednesday':'Budhavara','Thursday':'Guruvara','Friday':'Shukravara','Saturday':'Shanivara'}[data['weekday']])
                for field,expected in [('samvatsara',data['regional_metadata']['year']['samvatsara']),
                                      ('ritu',data['solar_ingress']['rutu']['en']),
                                      ('ayana',data['solar_ingress']['ayana']['en'])]:
                    self.record(case,sample,field,normalize(actual[field]),normalize(expected))
                # Month interval endpoints compare independently computed events.
                for field,source in [('lunar_month_start','start_jd'),('lunar_month_end','end_jd')]:
                    self.record(case,sample,field,jd(datetime.fromisoformat(actual[field]))*86400,month[source]*86400,seconds=True)
            else:
                for field in ('samvatsara','ritu','ayana'):
                    self.record(case,sample,field,None,None,reason='Source metadata describes sunrise; at_time does not expose this field')

    def report(self):
        totals=Counter()
        for counts in self.counts.values():totals.update(counts)
        return {'totals':dict(totals),'fields':{key:dict(value) for key,value in sorted(self.counts.items())},
                'timing_max_abs_seconds':{key:round(max(value),6) for key,value in sorted(self.differences.items())},
                'failures':self.failures,'uncertain_comparisons':self.uncertain}


def comparison_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def authorize_holdout(release_path,plan_hash,calculation_hashes,validator_hash,*,release=False,replay=False):
    if release_path.exists():
        record=json.loads(release_path.read_text())
        if not replay:
            raise ValueError('Holdout already inspected; only an explicitly labelled regression replay is permitted')
        if record['engine_hashes']!=calculation_hashes or record['comparator_sha256']!=validator_hash or record['plan_sha256']!=plan_hash:
            raise ValueError('Calculation code, comparator or plan changed after holdout release; collect new unseen cases')
        return 'regression_replay'
    if not release or replay:
        raise ValueError('Release the reserved answers explicitly after development is frozen')
    release_path.write_text(json.dumps({'released_utc':datetime.now(timezone.utc).isoformat(),
                                       'engine_hashes':calculation_hashes,'comparator_sha256':validator_hash,
                                       'plan_sha256':plan_hash,'note':'Answers are no longer unseen after this release.'},indent=2)+'\n')
    return 'first_holdout_evaluation'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=['development','holdout'],default='development')
    parser.add_argument('--allow-partial',action='store_true')
    parser.add_argument('--release-holdout',action='store_true')
    parser.add_argument('--replay-holdout',action='store_true')
    args=parser.parse_args();plan=json.loads(PLAN.read_text());cases=[c for c in plan['cases'] if c['split']==args.split]
    missing=[c for c in cases if not path_for(c).exists()]
    if missing and not args.allow_partial:raise SystemExit(f'{len(missing)} captures missing; collection must finish before a full report')
    REPORTS.mkdir(exist_ok=True)
    evaluation_kind='development'
    if args.split=='holdout':
        if args.allow_partial:raise SystemExit('Partial evaluation of reserved answers is prohibited')
        development_path=REPORTS/'development.json'
        if not development_path.exists():raise SystemExit('Complete development evaluation before opening reserved answers')
        development=json.loads(development_path.read_text())
        if (development['cases_evaluated']!=development['cases_expected'] or development['totals'].get('failed',0)
            or development['engine_hashes']!=engine_hashes() or development.get('comparator_sha256')!=comparison_hash()):
            raise SystemExit('Development report must be complete, current, and free of compared-field failures before holdout release')
        try:
            evaluation_kind=authorize_holdout(REPORTS/'holdout-release.json',hashlib.sha256(PLAN.read_bytes()).hexdigest(),
                                             engine_hashes(),comparison_hash(),release=args.release_holdout,replay=args.replay_holdout)
        except ValueError as exc:raise SystemExit(str(exc)) from exc
    comparison=Comparison();completed=[]
    for case in cases:
        if not path_for(case).exists():continue
        capture=read_capture(case)
        validate_capture(capture,case,plan)
        comparison.compare(case,capture,plan['cities'][case['city']]);completed.append(case)
    report={**comparison.report(),'split':args.split,'evaluation_kind':evaluation_kind,'comparator_sha256':comparison_hash(),'generated_utc':datetime.now(timezone.utc).isoformat(),
            'engine_hashes':engine_hashes(),'cases_evaluated':len(completed),'cases_expected':len(cases),'missing_cases':missing,
            'dates_by_city':{city:len([c for c in completed if c['city']==city]) for city in plan['cities']},
            'tolerance_seconds':TOLERANCE_SECONDS,
            'status':'incomplete' if missing else 'differences_found' if comparison.failures else 'no_failures_in_compared_fields',
            'limits':['One named external source, not independently audited ground truth.',
                      'Noon/evening Samvatsara/Ritu/Ayana are not independently supplied in source at_time metadata.',
                      'Nija and Kshaya classifications are not independently supplied as such by this response schema.',
                      'Near-transition labels are uncertain, never counted as passes.',
                      'Family wording and teacher audio review pending.'],
            'cases':completed}
    filename=args.split+'.json' if evaluation_kind!='regression_replay' else 'holdout-replay-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json'
    target=REPORTS/filename;target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({key:report[key] for key in ('status','cases_evaluated','cases_expected','dates_by_city','totals')},indent=2))
    print('Failure fields:',dict(Counter(f['field'] for f in comparison.failures)))
    print('Report:',target)
    if comparison.failures:raise SystemExit(1)


if __name__=='__main__':main()
