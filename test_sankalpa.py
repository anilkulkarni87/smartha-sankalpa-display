import re
import unittest
from datetime import datetime
from indic_transliteration import sanscript

import app
import sankalpa
from speech import SCHEMES, text_formats, canonical_text


class ExpandedSankalpaTests(unittest.TestCase):
    def test_all_calendar_names_have_recital_forms(self):
        for names,mapping in [(app.SAMVATSARA,sankalpa.YEAR),(app.MASA,sankalpa.MONTH),
                              (app.TITHI+['Amavasya'],sankalpa.TITHI),(app.NAK,sankalpa.NAKSHATRA),
                              (app.YOGA,sankalpa.YOGA),(app.KARANA+['Kimstughna','Shakuni','Chatushpada','Naga'],sankalpa.KARANA),
                              (app.VARA,sankalpa.VARA)]:
            self.assertFalse(set(names)-mapping.keys())

    def test_full_form_fills_all_fields_and_agrees_in_three_scripts(self):
        data=app.calculate(datetime.fromisoformat('2026-10-28T23:20:00-07:00'))
        formats=text_formats();outputs={}
        for script,scheme in SCHEMES.items():
            values={**data['recital'][script],'sandhya_action':formats['actions'][script]['morning']}
            text=re.sub(r'\{(\w+)\}',lambda m:values[m[1]],formats['full_templates'][script])
            self.assertNotRegex(text,r'[{}\[\]]')
            outputs[script]=sanscript.transliterate(text,scheme,sanscript.DEVANAGARI)
        self.assertEqual(outputs['roman'],outputs['sanskrit'])
        self.assertEqual(outputs['kannada'],outputs['sanskrit'])
        for value in ['पराभव नाम संवत्सरे','दक्षिणायने','शरदृतौ','आश्विनमासे',
                      'कृष्णपक्षे','चतुर्थ्यां शुभतिथौ','बुधवासरे','मृगशीर्षनक्षत्रे','परिघे योगे','बालवे करणे']:
            self.assertIn(value,outputs['sanskrit'])
        with self.assertRaisesRegex(ValueError,'100 syllables'):
            canonical_text(outputs['sanskrit'],'sanskrit')

    def test_recital_fields_change_with_tithi_and_weekday(self):
        a=app.calculate(datetime.fromisoformat('2026-10-28T23:20:00-07:00'))
        b=app.calculate(datetime.fromisoformat('2026-10-29T12:00:00-07:00'))
        self.assertNotEqual(a['recital']['sanskrit']['recital_tithi'],b['recital']['sanskrit']['recital_tithi'])
        self.assertNotEqual(a['recital']['sanskrit']['recital_vara'],b['recital']['sanskrit']['recital_vara'])


if __name__=='__main__':unittest.main()
