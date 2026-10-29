"""Offline tests of provenance and comparison accounting; no network requests."""
from copy import deepcopy
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from collect_reference import ENDPOINT, validate_capture
from validate_reference import Comparison, normalize, month_name, source_segment, authorize_holdout


class ReferenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.case={'city':'example','date':'2026-01-01','purpose':'test','split':'development'}
        self.plan={'profile':{'region':'kannada','sunrise_type':'centre'},
                   'cities':{'example':{'latitude':47.6101,'longitude':-122.2015,'timezone':'America/Los_Angeles'}}}
        request={**self.plan['profile'],'date':'2026-01-01','time':'12:00','lat':47.6101,'lon':-122.2015,'timezone':'America/Los_Angeles'}
        self.data={'date':'2026-01-01','timezone':'America/Los_Angeles','region':'kannada','calc_method':'drik','location':{'lat':47.6101,'lon':-122.2015}}
        raw=json.dumps(self.data)
        self.capture={'raw_response_utf8':raw,'data':self.data,
                      'provenance':{'endpoint':ENDPOINT,'request':request,'response_sha256':hashlib.sha256(raw.encode()).hexdigest()}}

    def test_raw_provenance_rejects_modified_facts(self):
        validate_capture(self.capture,self.case,self.plan)
        changed=deepcopy(self.capture);changed['data']['date']='2026-01-02'
        with self.assertRaisesRegex(ValueError,'payload'):validate_capture(changed,self.case,self.plan)
        changed=deepcopy(self.capture);changed['raw_response_utf8']+=' '
        with self.assertRaisesRegex(ValueError,'payload'):validate_capture(changed,self.case,self.plan)

    def test_capture_for_wrong_city_or_convention_is_rejected(self):
        changed=deepcopy(self.capture);changed['provenance']['request']['sunrise_type']='upper'
        with self.assertRaisesRegex(ValueError,'request'):validate_capture(changed,self.case,self.plan)
        changed=deepcopy(self.plan);changed['cities']['example']['latitude']=12.9716
        with self.assertRaisesRegex(ValueError,'request'):validate_capture(self.capture,self.case,changed)

    def test_missing_and_ambiguous_values_are_not_passes(self):
        comparison=Comparison()
        comparison.record(self.case,'noon','samvatsara',None,None,reason='Not supplied by source')
        comparison.record(self.case,'noon','tithi','a','b',uncertain=True)
        result=comparison.report()
        self.assertEqual(result['totals'],{'unavailable':1,'uncertain':1})
        self.assertFalse(result['failures']);self.assertEqual(len(result['uncertain_comparisons']),1)

    def test_numeric_tolerance_does_not_hide_label_mismatch(self):
        comparison=Comparison()
        comparison.record(self.case,'sunrise','sunrise',1000,940,seconds=True)
        comparison.record(self.case,'noon','tithi_end',1001,940,seconds=True)
        comparison.record(self.case,'noon','tithi','Pratipada','Dvitiya')
        result=comparison.report()
        self.assertEqual(result['totals'],{'passed':1,'failed':2})
        self.assertEqual({x['field'] for x in result['failures']},{'tithi_end','tithi'})

    def test_name_normalization_preserves_calendar_distinctions(self):
        for source,canonical in [('Śarat','Sharad'),('Pauṣa','Pausha'),('Tṛtīyā','Tritiya'),('Caturthī','Chaturthi'),
                                 ('Pūrvāṣāḍhā','Purva Ashadha'),('Gara','Garaja'),('Viśvavasu','Vishvavasu')]:
            self.assertEqual(normalize(source),normalize(canonical))
        self.assertEqual(month_name('Adhika Jyeṣṭha'),normalize('Jyeshtha'))
        self.assertNotEqual(normalize('Shukla'),normalize('Krishna'))
        self.assertNotEqual(normalize('Vasanta'),normalize('Grishma'))

    def test_reserved_answers_require_release_and_frozen_code(self):
        with TemporaryDirectory() as folder:
            target=Path(folder)/'release.json'
            args=(target,'plan-v1',{'app.py':'calculation-v1'},'validator-v1')
            with self.assertRaisesRegex(ValueError,'explicitly'):authorize_holdout(*args)
            self.assertFalse(target.exists())
            self.assertEqual(authorize_holdout(*args,release=True),'first_holdout_evaluation')
            with self.assertRaisesRegex(ValueError,'already inspected'):authorize_holdout(*args,release=True)
            self.assertEqual(authorize_holdout(*args,replay=True),'regression_replay')
            for changed in [(target,'plan-v2',args[2],args[3]),
                            (target,args[1],{'app.py':'calculation-v2'},args[3]),
                            (target,args[1],args[2],'validator-v2')]:
                with self.assertRaisesRegex(ValueError,'changed'):authorize_holdout(*changed,replay=True)

    def test_reference_intervals_use_the_active_segment(self):
        data={'day_sequence':{'tithis':[{'start_jd':1,'end_jd':2,'name':'Pratipada'},
                                       {'start_jd':2,'end_jd':3,'name':'Dvitiya'}]}}
        self.assertEqual(source_segment(data,'tithi',1.9)['name'],'Pratipada')
        self.assertEqual(source_segment(data,'tithi',2)['name'],'Dvitiya')
        self.assertIsNone(source_segment(data,'tithi',3.1))


if __name__=='__main__':unittest.main()
