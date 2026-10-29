"""Recital forms of Panchanga names, separate from the calendar's reference labels."""
from indic_transliteration import sanscript
from .speech import SCHEMES


def table(keys, values):
    keys, values = keys.split('|'), values.split('|')
    assert len(keys) == len(values)
    return dict(zip(keys, values))


YEAR = table(
    'Prabhava|Vibhava|Shukla|Pramoduta|Prajotpatti|Angirasa|Shrimukha|Bhava|Yuva|Dhata|Ishvara|Bahudhanya|Pramathi|Vikrama|Vrisha|Chitrabhanu|Svabhanu|Tarana|Parthiva|Vyaya|Sarvajit|Sarvadhari|Virodhi|Vikriti|Khara|Nandana|Vijaya|Jaya|Manmatha|Durmukhi|Hevilambi|Vilambi|Vikari|Sharvari|Plava|Shubhakrit|Shobhakrit|Krodhi|Vishvavasu|Parabhava|Plavanga|Kilaka|Saumya|Sadharana|Virodhikrit|Paridhavi|Pramadi|Ananda|Rakshasa|Nala|Pingala|Kalayukti|Siddharthi|Raudra|Durmati|Dundubhi|Rudhirodgari|Raktakshi|Krodhana|Akshaya',
    'प्रभव|विभव|शुक्ल|प्रमोदूत|प्रजोत्पत्ति|अङ्गिरस|श्रीमुख|भाव|युव|धातृ|ईश्वर|बहुधान्य|प्रमाथि|विक्रम|वृष|चित्रभानु|स्वभानु|तारण|पार्थिव|व्यय|सर्वजित्|सर्वधारि|विरोधि|विकृति|खर|नन्दन|विजय|जय|मन्मथ|दुर्मुखि|हेविलम्बि|विलम्बि|विकारि|शार्वरि|प्लव|शुभकृत्|शोभकृत्|क्रोधि|विश्वावसु|पराभव|प्लवङ्ग|कीलक|सौम्य|साधारण|विरोधिकृत्|परिधावि|प्रमादि|आनन्द|राक्षस|नल|पिङ्गल|कालयुक्ति|सिद्धार्थि|रौद्र|दुर्मति|दुन्दुभि|रुधिरोद्गारि|रक्ताक्षि|क्रोधन|अक्षय')
MONTH = table('Vaishakha|Jyeshtha|Ashadha|Shravana|Bhadrapada|Ashwina|Kartika|Margashirsha|Pausha|Magha|Phalguna|Chaitra',
              'वैशाख|ज्येष्ठ|आषाढ|श्रावण|भाद्रपद|आश्विन|कार्तिक|मार्गशीर्ष|पौष|माघ|फाल्गुन|चैत्र')
TITHI = table('Pratipada|Dvitiya|Tritiya|Chaturthi|Panchami|Shashthi|Saptami|Ashtami|Navami|Dashami|Ekadashi|Dvadashi|Trayodashi|Chaturdashi|Purnima|Amavasya',
              'प्रतिपदि|द्वितीयायां|तृतीयायां|चतुर्थ्यां|पञ्चम्यां|षष्ठ्यां|सप्तम्यां|अष्टम्यां|नवम्यां|दशम्यां|एकादश्यां|द्वादश्यां|त्रयोदश्यां|चतुर्दश्यां|पूर्णिमायां|अमावास्यायां')
NAKSHATRA = table('Ashwini|Bharani|Krittika|Rohini|Mrigashira|Ardra|Punarvasu|Pushya|Ashlesha|Magha|Purva Phalguni|Uttara Phalguni|Hasta|Chitra|Swati|Vishakha|Anuradha|Jyeshtha|Mula|Purva Ashadha|Uttara Ashadha|Shravana|Dhanishtha|Shatabhisha|Purva Bhadrapada|Uttara Bhadrapada|Revati',
                  'अश्विनी|भरणी|कृत्तिका|रोहिणी|मृगशीर्ष|आर्द्रा|पुनर्वसु|पुष्य|आश्लेषा|मघा|पूर्वफल्गुनी|उत्तरफल्गुनी|हस्त|चित्रा|स्वाती|विशाखा|अनुराधा|ज्येष्ठा|मूल|पूर्वाषाढा|उत्तराषाढा|श्रवण|धनिष्ठा|शतभिषा|पूर्वभाद्रपदा|उत्तरभाद्रपदा|रेवती')
YOGA = table('Vishkambha|Priti|Ayushman|Saubhagya|Shobhana|Atiganda|Sukarma|Dhriti|Shula|Ganda|Vriddhi|Dhruva|Vyaghata|Harshana|Vajra|Siddhi|Vyatipata|Variyana|Parigha|Shiva|Siddha|Sadhya|Shubha|Shukla|Brahma|Indra|Vaidhriti',
             'विष्कम्भे|प्रीतौ|आयुष्मति|सौभाग्ये|शोभने|अतिगण्डे|सुकर्मणि|धृतौ|शूले|गण्डे|वृद्धौ|ध्रुवे|व्याघाते|हर्षणे|वज्रे|सिद्धौ|व्यतीपाते|वरीयसि|परिघे|शिवे|सिद्धे|साध्ये|शुभे|शुक्ले|ब्रह्मणि|इन्द्रे|वैधृतौ')
KARANA = table('Bava|Balava|Kaulava|Taitila|Garaja|Vanija|Vishti|Kimstughna|Shakuni|Chatushpada|Naga',
               'बवे|बालवे|कौलवे|तैतिले|गरजे|वणिजि|विष्टौ|किंस्तुघ्ने|शकुनौ|चतुष्पदि|नागे')
VARA = table('Ravivara|Somavara|Mangalavara|Budhavara|Guruvara|Shukravara|Shanivara',
             'भानुवासरे|सोमवासरे|भौमवासरे|बुधवासरे|गुरुवासरे|शुक्रवासरे|शनिवासरे')
RITU = table('Vasanta|Grishma|Varsha|Sharad|Hemanta|Shishira',
             'वसन्तर्तौ|ग्रीष्मर्तौ|वर्षर्तौ|शरदृतौ|हेमन्तर्तौ|शिशिरर्तौ')


def recital_values(calendar):
    values = {
        'recital_samvatsara': YEAR.get(calendar['samvatsara'], '[संवत्सरं परीक्ष्यताम्]')+' नाम संवत्सरे',
        'recital_ayana': {'Uttarayana':'उत्तरायणे','Dakshinayana':'दक्षिणायने'}[calendar['ayana']],
        'recital_ritu': RITU[calendar['ritu']],
        'recital_masa': ('[मासं परीक्ष्यताम्]' if calendar.get('review_required') else {'adhika':'अधिक','nija':'निज'}.get(calendar.get('month_type'),'')+MONTH[calendar['masa']]+'मासे'),
        'recital_paksha': {'Shukla':'शुक्लपक्षे','Krishna':'कृष्णपक्षे'}[calendar['paksha']],
        'recital_tithi': TITHI[calendar['tithi']]+' शुभतिथौ',
        'recital_vara': VARA[calendar['vara']],
        'recital_nakshatra': NAKSHATRA[calendar['nakshatra']]+'नक्षत्रे',
        'recital_yoga': YOGA[calendar['yoga']]+' योगे',
        'recital_karana': KARANA[calendar['karana']]+' करणे',
    }
    return {script: {key: sanscript.transliterate(value, sanscript.DEVANAGARI, scheme)
                     for key, value in values.items()} for script, scheme in SCHEMES.items()}
