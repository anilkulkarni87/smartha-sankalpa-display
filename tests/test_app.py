"""Location and sunrise regression tests: python -m unittest -v."""
from datetime import datetime, timedelta
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from fastapi.testclient import TestClient
from sankalpa_display.api import app
from sankalpa_display.locations import CITIES


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)

    def calendar(self, city='bellevue', at='2026-10-28T12:00:00-07:00'):
        response=self.client.get('/api/panchanga',params={'city':city,'at':at})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_location_catalogue_and_validation(self):
        response=self.client.get('/api/locations')
        self.assertEqual(len(response.json()),len(CITIES))
        self.assertEqual(self.client.get('/api/panchanga?city=unknown').status_code,422)
        self.assertEqual(self.client.get('/api/panchanga?at=bad').status_code,422)

    def test_all_cities_have_local_sunrise_and_day_boundary(self):
        for city, location in CITIES.items():
            with self.subTest(city=city):
                result=self.calendar(city, '2026-10-28T12:00:00')
                rise=datetime.fromisoformat(result['sunrise'])
                self.assertEqual(rise.date().isoformat(),'2026-10-28')
                self.assertEqual(result['timezone'],location['timezone'])
                sunrise=self.calendar(city,result['sunrise'])
                self.assertEqual(sunrise['panchanga_date'],'2026-10-28')
                before=self.calendar(city,(rise-timedelta(seconds=1)).isoformat())
                self.assertEqual(before['panchanga_date'],'2026-10-27')

    def test_city_switch_keeps_same_instant_and_changes_sunrise(self):
        bellevue=self.calendar()
        bengaluru=self.calendar('bengaluru')
        bellevue_again=self.calendar()
        for field in ('tithi','nakshatra','yoga','karana'):
            self.assertEqual(bellevue[field],bengaluru[field])
        self.assertEqual(bellevue,bellevue_again)
        self.assertNotEqual(bellevue['sunrise'],bengaluru['sunrise'])
        self.assertEqual(datetime.fromisoformat(bengaluru['timestamp']).utcoffset(),timedelta(hours=5,minutes=30))

    def test_thursday_vara_and_recital_start_at_local_midnight(self):
        wednesday=self.calendar(at='2026-10-28T23:59:59-07:00')
        self.assertEqual(wednesday['vara'],'Budhavara')
        for at in ('2026-10-29T00:00:00-07:00','2026-10-29T07:40:00-07:00',
                   '2026-10-29T08:00:00-07:00','2026-10-29T14:40:00Z'):
            with self.subTest(at=at):
                thursday=self.calendar(at=at)
                self.assertEqual(thursday['vara'],'Guruvara')
                self.assertEqual(thursday['recital']['sanskrit']['recital_vara'],'गुरुवासरे')
                self.assertEqual(thursday['family_recital']['sanskrit']['family_vara'],'गुरु (बृहस्पति) वासरे')
        # Sunrise-day metadata is retained, but does not set the displayed Vara.
        self.assertEqual(self.calendar(at='2026-10-29T07:40:00-07:00')['panchanga_date'],'2026-10-28')

    def test_dst_and_southern_hemisphere_timezones(self):
        for city, before, after, offset1, offset2 in [
            ('bellevue','2026-03-07T12:00:00','2026-03-09T12:00:00',-8,-7),
            ('sydney','2026-10-03T12:00:00','2026-10-05T12:00:00',10,11),
        ]:
            a=self.calendar(city,before);b=self.calendar(city,after)
            self.assertEqual(datetime.fromisoformat(a['sunrise']).utcoffset(),timedelta(hours=offset1))
            self.assertEqual(datetime.fromisoformat(b['sunrise']).utcoffset(),timedelta(hours=offset2))

    def test_home_is_file_relative(self):
        original=Path.cwd()
        with TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                response=self.client.get('/')
                javascript=self.client.get('/static/app.js')
                stylesheet=self.client.get('/static/styles.css')
            finally:
                os.chdir(original)
        self.assertEqual(response.status_code,200)
        self.assertIn('Yajurveda',response.text)
        self.assertIn('/static/app.js',response.text)
        self.assertIn('/static/styles.css',response.text)
        self.assertEqual(javascript.status_code,200)
        self.assertIn('renderRecital',javascript.text)
        self.assertEqual(stylesheet.status_code,200)
        self.assertIn('.recital-calendar',stylesheet.text)
        self.assertEqual(response.headers['cache-control'],'no-store')


if __name__=='__main__':
    unittest.main()
