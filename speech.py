"""Sanskrit text formats and on-demand Vagdhenu generation with a local WAV cache."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import hashlib
import base64
import json
import os
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
from threading import Lock
import unicodedata
import wave

from indic_transliteration import sanscript

SCHEMES = {'roman': sanscript.IAST, 'sanskrit': sanscript.DEVANAGARI,
           'kannada': sanscript.KANNADA}
OPENING = 'मम उपात्त समस्त दुरितक्षयद्वारा\nश्रीपरमेश्वरप्रीत्यर्थं\n'
ACTIONS = {'morning': 'प्रातः सन्ध्याम् उपासिष्ये',
           'noon': 'माध्याह्निकं करिष्ये', 'evening': 'सायं सन्ध्याम् उपासिष्ये'}
FULL_TEMPLATE = '''ममोपात्तसमस्तदुरितक्षयद्वारा श्रीपरमेश्वरमुद्दिश्य श्रीपरमेश्वरप्रीत्यर्थं,
शुभे शोभने मुहूर्ते श्रीमहाविष्णोराज्ञया प्रवर्तमानस्य,
अद्य ब्रह्मणः द्वितीयपरार्धे, श्वेतवराहकल्पे,
वैवस्वतमन्वन्तरे, कलियुगे, प्रथमे पादे,
अस्मिन् शुभस्थाने,
वर्तमानव्यावहारिकचान्द्रमानेन,
{recital_samvatsara}, {recital_ayana}, {recital_ritu},
{recital_masa}, {recital_paksha}, {recital_tithi},
{recital_vara}, {recital_nakshatra},
{recital_yoga}, {recital_karana},
एवं गुणविशेषणविशिष्टायामस्यां शुभतिथौ,
श्रीपरमेश्वरप्रीत्यर्थं मम श्रौतस्मार्तनित्यकर्मानुष्ठानयोग्यतासिद्ध्यर्थं,
{sandhya_action} ॥'''


def text_formats():
    templates, actions, full_templates = {}, {}, {}
    for script, scheme in SCHEMES.items():
        templates[script] = sanscript.transliterate(OPENING, sanscript.DEVANAGARI, scheme) + '{sandhya_action} ॥'
        actions[script] = {key: sanscript.transliterate(value, sanscript.DEVANAGARI, scheme)
                           for key, value in ACTIONS.items()}
        full_templates[script] = ''.join(part if part.startswith('{') else
            sanscript.transliterate(part, sanscript.DEVANAGARI, scheme)
            for part in re.split(r'(\{\w+\})', FULL_TEMPLATE))
    return {'templates': templates, 'actions': actions, 'full_templates': full_templates}


def canonical_text(text, script):
    if script not in SCHEMES:
        raise ValueError('Choose English transliteration, Sanskrit or Kannada.')
    text = unicodedata.normalize('NFC', text.strip())
    if not text or len(text) > 4000:
        raise ValueError('Enter a Sankalpa of 1–4000 characters.')
    if any(char in text for char in '{}[]'):
        raise ValueError('Complete missing template fields before generating audio.')
    text = sanscript.transliterate(text, SCHEMES[script], sanscript.DEVANAGARI)
    text = ' '.join(text.replace('-', ' ').replace('।।', '॥').split())
    if not any('\u0900' <= c <= '\u097f' for c in text):
        raise ValueError('Audio requires Sanskrit text, not an English translation.')
    if any(c.isalpha() and not '\u0900' <= c <= '\u097f' for c in text):
        raise ValueError('Use Sanskrit in Devanagari, Kannada, or IAST transliteration; remove English notes.')
    syllables = sum(1 for i, c in enumerate(text)
                    if '\u0905' <= c <= '\u0914'
                    or ('\u0915' <= c <= '\u0939' and (i+1 == len(text) or text[i+1] != '्')))
    if syllables > 100 or text.count('॥') >= 2:
        raise ValueError('The public Vagdhenu demo accepts at most 100 syllables and one passage per request. Shorten the text or configure your own Vagdhenu service.')
    return text


def render_vagdhenu(text, destination, source):
    # Imported only when generation is requested. No model weights run on the display device.
    from gradio_client import Client
    with TemporaryDirectory(prefix='vagdhenu-', dir=destination.parent) as temporary:
        client = Client(source, token=os.environ.get('HF_TOKEN') or None, verbose=False,
                        download_files=temporary, httpx_kwargs={'timeout': 60},
                        analytics_enabled=False)
        job = client.submit(text, 'gadya', 60, api_name='/synthesize')
        try:
            result = job.result(timeout=240)
        except FutureTimeout as exc:
            job.cancel()
            raise RuntimeError('Vagdhenu timed out. Try again later; no automatic retries were sent.') from exc
        audio = Path(result[0])
        if audio.stat().st_size > 25_000_000:
            raise RuntimeError('Vagdhenu returned an unexpectedly large audio file.')
        with wave.open(str(audio), 'rb') as wav:
            if wav.getnframes() == 0:
                raise RuntimeError('Vagdhenu returned empty audio.')
        staged = destination.with_suffix('.tmp')
        shutil.copyfile(audio, staged)
        staged.replace(destination)


class AudioService:
    def __init__(self, cache_dir=None, renderer=render_vagdhenu):
        self.cache = Path(cache_dir or Path(__file__).with_name('.audio-cache'))
        self.source = os.environ.get('VAGDHENU_SPACE', 'prathoshap/vagdhenu-demo')
        self.renderer = renderer
        self.jobs = {}
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vagdhenu')

    @staticmethod
    def provider_error(exc):
        message=str(exc) or type(exc).__name__
        token=os.environ.get('HF_TOKEN')
        if token:
            message=message.replace(token,'[redacted]')
        return 'Vagdhenu could not generate audio: '+message[:500]

    def generate_inline(self, text, script):
        """Return audio within this request; no shared job state or disk cache."""
        text=canonical_text(text,script)
        key=hashlib.sha256(json.dumps([self.source,'gadya',60,text],ensure_ascii=False).encode()).hexdigest()
        try:
            with TemporaryDirectory(prefix='sankalpa-audio-') as folder:
                destination=Path(folder)/'calendar.wav'
                self.renderer(text,destination,self.source)
                # Base64 expands by 4/3; stay below Vercel's 4.5 MB response cap.
                if destination.stat().st_size>3_000_000:
                    raise RuntimeError('Audio is too large for hosted playback. Generate it on the local app instead.')
                with wave.open(str(destination),'rb') as wav:
                    if not wav.getnframes():
                        raise RuntimeError('The audio recording is empty.')
                encoded=base64.b64encode(destination.read_bytes()).decode('ascii')
            return {'id':key,'state':'ready','url':'data:audio/wav;base64,'+encoded,'cached':False}
        except Exception as exc:
            return {'id':key,'state':'error','error':self.provider_error(exc)}

    def start(self, text, script):
        text = canonical_text(text, script)
        key = hashlib.sha256(json.dumps([self.source, 'gadya', 60, text], ensure_ascii=False).encode()).hexdigest()
        self.cache.mkdir(parents=True, exist_ok=True)
        with self.lock:
            if (self.cache / (key+'.wav')).is_file():
                return {'id': key, 'state': 'ready', 'url': f'/api/audio/{key}/file', 'cached': True}
            if key in self.jobs and self.jobs[key]['state'] != 'error':
                return dict(self.jobs[key])
            if sum(j['state'] in ('queued', 'generating') for j in self.jobs.values()) >= 3:
                raise RuntimeError('Audio generation is busy. Wait for the current jobs to finish.')
            self.jobs[key] = {'id': key, 'state': 'queued', 'cached': False}
            self.executor.submit(self._generate, key, text)
            return dict(self.jobs[key])

    def _generate(self, key, text):
        with self.lock:
            self.jobs[key]['state'] = 'generating'
        try:
            self.renderer(text, self.cache / (key+'.wav'), self.source)
            with self.lock:
                self.jobs[key].update(state='ready', url=f'/api/audio/{key}/file')
        except Exception as exc:
            # Keep server credentials out of errors, including messages from the remote client.
            with self.lock:
                self.jobs[key].update(state='error', error=self.provider_error(exc))

    def status(self, key):
        if not re.fullmatch(r'[a-f0-9]{64}', key):
            raise KeyError(key)
        with self.lock:
            if (self.cache / (key+'.wav')).is_file():
                return {'id': key, 'state': 'ready', 'url': f'/api/audio/{key}/file'}
            if key not in self.jobs:
                raise KeyError(key)
            return dict(self.jobs[key])


audio_service = AudioService()
