"""Recorded external comparisons plus numerical/convention regressions.

Only the JSON fixtures are comparisons with externally observed day boards.
The year sweep checks internal invariants, not independent astronomical accuracy.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from indic_transliteration import sanscript
from sankalpa_display import api as app
from sankalpa_display import calendar
from sankalpa_display.locations import CITIES
from sankalpa_display.lunisolar import (jd, dt_jd, conjunction, lunation_at, month_info,
                       sunrise_for, year_boundary)
from sankalpa_display.speech import SCHEMES


class LunisolarTests(unittest.TestCase):
    def test_recorded_drikganita_comparisons(self):
        fixtures=sorted((Path(__file__).resolve().parents[1]/'validation').glob('drikganita-*-bellevue.json'))
        self.assertEqual(len(fixtures),3)
        for path in fixtures:
            fixture=json.loads(path.read_text());reference=fixture['reference']
            actual=calendar.calculate(datetime.fromisoformat(fixture['app_sample']))
            with self.subTest(date=fixture['date']):
                for key in ('samvatsara','masa','ritu','ayana','paksha','tithi','nakshatra','yoga','karana'):
                    self.assertEqual(actual[key],reference[key],key)
                self.assertEqual(actual['is_adhika'],reference['adhika'])
                for key in ('sunrise','tithi_ends','nakshatra_ends','yoga_ends','karana_ends'):
                    found=datetime.fromisoformat(actual[key])
                    expected=datetime.fromisoformat(fixture['date']+'T'+reference[key+'_hhmm']).replace(tzinfo=found.tzinfo)+timedelta(days=fixture.get('reference_day_offsets',{}).get(key,0))
                    self.assertLessEqual(abs((found-expected).total_seconds()),60,key)

    def test_adhika_nija_recital_in_all_scripts(self):
        for date,kind,prefix in [('2026-05-25T12:00:00-07:00','adhika','अधिक'),
                                 ('2026-06-20T12:00:00-07:00','nija','निज')]:
            data=calendar.calculate(datetime.fromisoformat(date))
            self.assertEqual(data['masa'],'Jyeshtha');self.assertEqual(data['month_type'],kind)
            for script,scheme in SCHEMES.items():
                deva=sanscript.transliterate(data['recital'][script]['recital_masa'],scheme,sanscript.DEVANAGARI)
                self.assertEqual(deva,prefix+'ज्येष्ठमासे')

    def test_new_moon_boundaries_and_tithi_wrap(self):
        index=lunation_at(jd(datetime.fromisoformat('2026-05-25T12:00:00-07:00')))
        for index in (index,index+1,index+2):
            event=conjunction(index)
            before=calendar.calculate(dt_jd(event)-timedelta(seconds=1))
            after=calendar.calculate(dt_jd(event)+timedelta(seconds=1))
            self.assertEqual(before['tithi'],'Amavasya');self.assertEqual(after['tithi'],'Pratipada')
            self.assertNotEqual(before['month_type'],after['month_type'])
            self.assertEqual(datetime.fromisoformat(before['lunar_month_end']),datetime.fromisoformat(after['lunar_month_start']))

    def test_adhika_chaitra_does_not_start_new_year(self):
        place=CITIES['bengaluru']
        a=calendar.calculate(datetime.fromisoformat('2029-03-20T12:00:00+05:30'),place)
        self.assertEqual((a['masa_display'],a['samvatsara']),('Adhika Chaitra','Kilaka'))
        boundary=year_boundary(2029,place)
        self.assertEqual(dt_jd(boundary).astimezone(ZoneInfo(place['timezone'])).date().isoformat(),'2029-04-14')
        before=calendar.calculate(dt_jd(boundary)-timedelta(seconds=1),place)
        after=calendar.calculate(dt_jd(boundary)+timedelta(seconds=1),place)
        self.assertEqual(before['samvatsara'],'Kilaka');self.assertEqual(after['samvatsara'],'Saumya')
        self.assertEqual(after['masa_display'],'Nija Chaitra')

    def test_year_convention_is_explicit(self):
        place=CITIES['bellevue']
        conjunction_boundary=year_boundary(2026,place,year_convention='conjunction')
        sunrise_boundary=year_boundary(2026,place,year_convention='sunrise')
        self.assertNotEqual(conjunction_boundary,sunrise_boundary)
        middle=dt_jd((conjunction_boundary+sunrise_boundary)/2)
        self.assertNotEqual(calendar.calculate(middle,place,year_mode='conjunction')['samvatsara'],
                            calendar.calculate(middle,place,year_mode='sunrise')['samvatsara'])

    def test_skipped_pratipada_does_not_advance_year_before_new_moon(self):
        # DrikGanita: Apr 10 2032 at Bengaluru sunrise is Amavasya / Virodhikrit;
        # Apr 11 sunrise is Dvitiya / Paridhavi. No Pratipada touches a sunrise.
        place=CITIES['bengaluru']
        sample=datetime.fromisoformat('2032-04-10T06:20:00+05:30')
        for mode in ('conjunction','sunrise'):
            result=calendar.calculate(sample,place,year_mode=mode)
            self.assertEqual((result['tithi'],result['samvatsara']),('Amavasya','Virodhikrit'))
        boundary=year_boundary(2032,place,year_convention='conjunction')
        before=calendar.calculate(dt_jd(boundary)-timedelta(seconds=1),place)
        after=calendar.calculate(dt_jd(boundary)+timedelta(seconds=1),place)
        self.assertEqual(before['samvatsara'],'Virodhikrit');self.assertEqual(after['samvatsara'],'Paridhavi')
        sunrise_boundary=dt_jd(year_boundary(2032,place,year_convention='sunrise')).astimezone(ZoneInfo(place['timezone']))
        self.assertEqual(sunrise_boundary.date().isoformat(),'2032-04-11')
        self.assertEqual(calendar.calculate(sunrise_boundary,place,year_mode='sunrise')['tithi'],'Dvitiya')

    def test_kshaya_magha_1983_requires_recital_review(self):
        data=calendar.calculate(datetime.fromisoformat('1983-02-01T12:00:00+05:30'),CITIES['bengaluru'])
        self.assertEqual(data['month_type'],'kshaya');self.assertEqual(data['omitted_month'],'Magha')
        self.assertEqual(data['solar_ingresses_in_month'],2)
        self.assertTrue(data['review_required']);self.assertTrue(data['warnings'])
        self.assertIn('[',data['recital']['sanskrit']['recital_masa'])

    def test_reported_transition_times_change_the_active_field(self):
        sample=calendar.calculate(datetime.fromisoformat('2026-10-28T08:00:00-07:00'))
        for field in ('tithi','nakshatra','yoga','karana'):
            boundary=datetime.fromisoformat(sample[field+'_ends'])
            before=calendar.calculate(boundary-timedelta(seconds=2))
            after=calendar.calculate(boundary+timedelta(seconds=2))
            self.assertEqual(before[field],sample[field])
            self.assertNotEqual(before[field],after[field])

    def test_2026_daily_intervals_two_cities(self):
        for city in ('bellevue','bengaluru'):
            place=CITIES[city];tz=ZoneInfo(place['timezone'])
            first=datetime(2026,1,1,tzinfo=tz)
            for n in range(365):
                day=first+timedelta(days=n)
                rise=sunrise_for(day.date(),place)
                for moment in (rise,day.replace(hour=12),day.replace(hour=18)):
                    value=jd(moment);month=month_info(value)
                    self.assertLessEqual(month['start'],value);self.assertLess(value,month['end'])
                    self.assertEqual(month['solar_ingresses'],{'adhika':0,'normal':1,'nija':1,'kshaya':2}[month['kind']])
                    self.assertLess(abs((value-month['start'])/29.6),1.1)

    def test_api_profiles_are_validated_and_do_not_leak(self):
        client=TestClient(app.app)
        query={'at':'2026-05-25T06:00:00-07:00'}
        a=client.get('/api/panchanga',params=query).json()
        b=client.get('/api/panchanga',params={**query,'sunrise_mode':'apparent','ritu_mode':'lunar','year_mode':'sunrise'}).json()
        c=client.get('/api/panchanga',params=query).json()
        self.assertEqual(a,c);self.assertNotEqual(a['sunrise'],b['sunrise'])
        self.assertEqual((a['conventions']['year'],b['conventions']['year']),('conjunction','sunrise'))
        self.assertEqual((a['ritu'],b['ritu']),('Vasanta','Grishma'))
        for params in ({'sunrise_mode':'bogus'},{'ritu_mode':'bogus'},{'year_mode':'bogus'},{'at':'1800-01-01T12:00:00Z'}):
            self.assertEqual(client.get('/api/panchanga',params=params).status_code,422)


if __name__=='__main__':unittest.main()
