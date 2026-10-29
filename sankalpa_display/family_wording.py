"""User-supplied US family wording from the October 29 screenshot.

The user confirmed retaining the existing Yajurveda opening/session closing,
with this geography used only for US cities. This records their chosen wording;
it does not assert teacher review or certify ritual geography.
"""
import re
from indic_transliteration import sanscript
from .speech import SCHEMES, FULL_TEMPLATE
from .wording import MONTH

# Fixed prose is transcribed from the screenshot; the pictured calendar values
# are examples and are replaced with computed recital fields below.
FAMILY_SECTION_KANNADA = '''ಕ್ರೌಂಚ ದ್ವೀಪೇ, ರಮಣಕ ವರ್ಷೇ, ಐಂದ್ರಿಕ ಖಂಡೇ,
ಸಪ್ತ ಸಮುದ್ರಾಂತರೇ, ಕಪಿಲಾರಣ್ಯೇ ಶೋಭನ ಗೃಹೇ,
ಸಮಸ್ತ ದೇವತಾ ಬ್ರಾಹ್ಮಣ, ಹರಿಹರ ಗುರುಚರಣ ಸನ್ನಿಧೌ,
ಅಸ್ಮಿನ್ ವರ್ತಮಾನ ವ್ಯಾವಹಾರಿಕ ಚಾಂದ್ರಮಾನೇನ,
ಪ್ರಭವಾದಿ ಷಷ್ಟಿ ಸಂವತ್ಸರಾಣಾಂ ಮಧ್ಯೇ,
ಶ್ರೀ {recital_samvatsara}, {recital_ayana}, {recital_ritu},
{family_masa}, {recital_paksha}, {family_tithi},
{family_vara}, {recital_nakshatra},
ಶುಭ ನಕ್ಷತ್ರೇ ಶುಭ ಯೋಗ ಶುಭ ಕರಣ,
ಏವಂಗುಣ ವಿಶೇಷಣ ವಿಶಿಷ್ಟಾಯಾಂ ಶುಭ ತಿಥೌ,'''
TITHI_NOUNS=dict(zip(
    ['Pratipada','Dvitiya','Tritiya','Chaturthi','Panchami','Shashthi','Saptami','Ashtami','Navami','Dashami','Ekadashi','Dvadashi','Trayodashi','Chaturdashi','Purnima','Amavasya'],
    ['प्रतिपदा','द्वितीया','तृतीया','चतुर्थी','पञ्चमी','षष्ठी','सप्तमी','अष्टमी','नवमी','दशमी','एकादशी','द्वादशी','त्रयोदशी','चतुर्दशी','पूर्णिमा','अमावास्या']))
WEEKDAYS=dict(zip(
    ['Ravivara','Somavara','Mangalavara','Budhavara','Guruvara','Shukravara','Shanivara'],
    ['रवि','सोम','मङ्गल','बुध','गुरु (बृहस्पति)','शुक्र','शनि']))


def transliterate_template(text,source,target):
    return ''.join(part if part.startswith('{') else sanscript.transliterate(part,source,target)
                   for part in re.split(r'(\{\w+\})',text))


def family_templates():
    opening_marker='अस्मिन् शुभस्थाने,'
    closing_marker='एवं गुणविशेषणविशिष्टायामस्यां शुभतिथौ,\n'
    if FULL_TEMPLATE.count(opening_marker)!=1 or FULL_TEMPLATE.count(closing_marker)!=1:
        raise ValueError('Review the family template after changing the built-in opening/closing')
    opening=FULL_TEMPLATE.split(opening_marker,1)[0]
    closing=FULL_TEMPLATE.split(closing_marker,1)[1]
    section=transliterate_template(FAMILY_SECTION_KANNADA,sanscript.KANNADA,sanscript.DEVANAGARI)
    canonical=opening+section+'\n'+closing
    return {script:transliterate_template(canonical,sanscript.DEVANAGARI,scheme)
            for script,scheme in SCHEMES.items()}


def family_values(calendar):
    # Ashwayuja is the family's supplied synonym for the Ashwina lunar month;
    # it changes recital wording, never the underlying month calculation.
    name='आश्वयुज' if calendar['masa']=='Ashwina' else MONTH[calendar['masa']]
    prefix={'adhika':'अधिक ','nija':'निज '}.get(calendar.get('month_type'),'')
    values={
        'family_masa':'[मासं परीक्ष्यताम्]' if calendar.get('review_required') else prefix+name+' मासे',
        'family_tithi':{'Shukla':'शुक्ल','Krishna':'कृष्ण'}[calendar['paksha']]+' '+TITHI_NOUNS[calendar['tithi']]+' तिथौ',
        'family_vara':WEEKDAYS[calendar['vara']]+' वासरे',
    }
    return {script:{key:sanscript.transliterate(value,sanscript.DEVANAGARI,scheme) for key,value in values.items()}
            for script,scheme in SCHEMES.items()}


def calendar_audio_text(calendar):
    """Only the eight changing phrases requested for daily audio playback."""
    if calendar.get('review_required'):
        return {}
    keys=('recital_samvatsara','recital_ayana','recital_ritu','family_masa',
          'recital_paksha','family_tithi','family_vara','recital_nakshatra')
    result={}
    for script,scheme in SCHEMES.items():
        values={**calendar['recital'][script],**calendar['family_recital'][script]}
        result[script]=sanscript.transliterate('श्री ',sanscript.DEVANAGARI,scheme)+', '.join(values[key] for key in keys)+' ।'
    return result
