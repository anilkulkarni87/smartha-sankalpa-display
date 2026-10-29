import re
import unittest
from datetime import datetime
from fastapi.testclient import TestClient
from indic_transliteration import sanscript
import app
from family_wording import family_templates, TITHI_NOUNS
from speech import SCHEMES, text_formats, canonical_text


def render(moment,script='sanskrit',mode='morning'):
    data=app.calculate(datetime.fromisoformat(moment))
    values={**data['recital'][script],**data['family_recital'][script],
            'sandhya_action':text_formats()['actions'][script][mode]}
    return re.sub(r'\{(\w+)\}',lambda m:values[m[1]],family_templates()[script])


class FamilyWordingTests(unittest.TestCase):
    def test_family_section_and_existing_opening_closing_agree_in_three_scripts(self):
        outputs={}
        for script,scheme in SCHEMES.items():
            text=render('2026-10-29T12:00:00-07:00',script)
            self.assertNotRegex(text,r'[{}\[\]]')
            outputs[script]=sanscript.transliterate(text,scheme,sanscript.DEVANAGARI)
        self.assertEqual(outputs['roman'],outputs['sanskrit'])
        self.assertEqual(outputs['kannada'],outputs['sanskrit'])
        text=outputs['sanskrit']
        self.assertIn('ममोपात्तसमस्तदुरितक्षयद्वारा',text)
        for fragment in ('क्रौंच द्वीपे','रमणक वर्षे','ऐंद्रिक खंडे','कपिलारण्ये शोभन गृहे',
                         'श्री पराभव नाम संवत्सरे','आश्वयुज मासे','गुरु (बृहस्पति) वासरे'):
            self.assertIn(fragment,text)
        self.assertEqual(text.count('प्रातः सन्ध्याम् उपासिष्ये'),1)
        self.assertNotIn('अस्मिन् शुभस्थाने',text)

    def test_picture_calendar_values_are_not_frozen(self):
        first=render('2026-10-28T08:00:00-07:00')
        second=render('2026-10-29T12:00:00-07:00',mode='noon')
        self.assertIn('कृष्ण तृतीया तिथौ',first);self.assertIn('बुध वासरे',first)
        self.assertIn('कृष्ण पञ्चमी तिथौ',second);self.assertIn('गुरु (बृहस्पति) वासरे',second)
        self.assertIn('माध्याह्निकं करिष्ये',second)
        self.assertIn('रोहिणीनक्षत्रे',first);self.assertIn('मृगशीर्षनक्षत्रे',second)
        # The user's generic Yoga/Karana phrase remains as supplied.
        self.assertIn('शुभ योग शुभ करण',second)

    def test_leap_qualifiers_and_all_tithi_names_are_available(self):
        self.assertEqual(set(TITHI_NOUNS),set(app.TITHI+['Amavasya']))
        self.assertIn('अधिक ज्येष्ठ मासे',render('2026-05-25T12:00:00-07:00'))
        self.assertIn('निज ज्येष्ठ मासे',render('2026-06-20T12:00:00-07:00'))

    def test_api_records_scope_and_does_not_bypass_audio_limit(self):
        formats=TestClient(app.app).get('/api/text-formats').json()
        self.assertEqual(formats['family_profile']['scope'],'United States')
        self.assertEqual(formats['family_profile']['teacher_review'],'pending')
        self.assertEqual(set(formats['family_templates']),set(SCHEMES))
        with self.assertRaisesRegex(ValueError,'100 syllables'):
            canonical_text(render('2026-10-29T12:00:00-07:00'),'sanskrit')

    def test_edited_template_converts_all_scripts_without_audio_length_limit(self):
        client=TestClient(app.app)
        for script in SCHEMES:
            source=family_templates()[script]
            response=client.post('/api/template-formats',json={'text':source,'script':script})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['templates'],family_templates())

    def test_edited_template_rejects_broken_or_unknown_placeholders(self):
        client=TestClient(app.app)
        for source in ('   ','{unknown}','{recital_vara','recital_vara}'):
            self.assertEqual(client.post('/api/template-formats',json={'text':source,'script':'sanskrit'}).status_code,422)

    def test_calendar_audio_contains_only_requested_fields_in_all_scripts(self):
        data=app.calculate(datetime.fromisoformat('2026-10-29T08:30:00-07:00'))
        expected='श्री पराभव नाम संवत्सरे, दक्षिणायने, शरदृतौ, आश्वयुज मासे, कृष्णपक्षे, कृष्ण चतुर्थी तिथौ, गुरु (बृहस्पति) वासरे, मृगशीर्षनक्षत्रे ।'
        for script in SCHEMES:
            self.assertEqual(canonical_text(data['calendar_audio'][script],script),expected)
        # Changed tithi must produce a different cache input even on the same day.
        later=app.calculate(datetime.fromisoformat('2026-10-29T12:00:00-07:00'))
        self.assertNotEqual(data['calendar_audio'],later['calendar_audio'])
        self.assertIn('कृष्ण पञ्चमी तिथौ',later['calendar_audio']['sanskrit'])
        self.assertNotIn('ममोपात्त',expected)

    def test_kshaya_calendar_audio_is_withheld(self):
        from family_wording import calendar_audio_text
        self.assertEqual(calendar_audio_text({'review_required':True}),{})


if __name__=='__main__':unittest.main()
