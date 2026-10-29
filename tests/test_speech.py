from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import wave
import base64

from fastapi.testclient import TestClient
from sankalpa_display import api as app
from sankalpa_display.speech import AudioService, canonical_text, text_formats


def sample(script='sanskrit', mode='morning'):
    formats=text_formats()
    return formats['templates'][script].replace('{sandhya_action}',formats['actions'][script][mode])


def write_test_wav(path):
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000)
        wav.writeframes(b'\x00\x00'*240)


class SpeechTests(unittest.TestCase):
    def test_three_scripts_preserve_same_sanskrit_in_all_sessions(self):
        for mode in ('morning','noon','evening'):
            expected=canonical_text(sample('sanskrit',mode),'sanskrit')
            for script in ('roman','sanskrit','kannada'):
                self.assertEqual(canonical_text(sample(script,mode),script),expected)

    def test_rejects_missing_fields_notes_and_public_demo_oversize(self):
        for text,script in [('{gotra}','roman'),('[please set]','roman'),('Hello world','roman'),
                            ('राम '*101,'sanskrit'),('राम ॥ राम ॥','sanskrit')]:
            with self.subTest(text=text[:20]),self.assertRaises(ValueError):
                canonical_text(text,script)

    def test_generation_cache_shared_by_scripts_and_survives_restart(self):
        calls=[]
        def renderer(text,path,source):
            calls.append(text);write_test_wav(path)
        with TemporaryDirectory() as folder:
            service=AudioService(folder,renderer)
            job=service.start(sample(),'sanskrit')
            service.executor.shutdown(wait=True)
            self.assertEqual(service.status(job['id'])['state'],'ready')
            for script in ('roman','kannada'):
                cached=AudioService(folder,renderer)
                self.assertTrue(cached.start(sample(script),script)['cached'])
                cached.executor.shutdown(wait=True)
            self.assertEqual(len(calls),1)

    def test_changed_session_gets_a_different_audio_key(self):
        with TemporaryDirectory() as folder:
            service=AudioService(folder,lambda text,path,source:write_test_wav(path))
            morning=service.start(sample(),'sanskrit')
            noon=service.start(sample(mode='noon'),'sanskrit')
            service.executor.shutdown(wait=True)
            self.assertNotEqual(morning['id'],noon['id'])

    def test_provider_error_is_visible_and_credentials_are_redacted(self):
        def failing(*args):raise RuntimeError('quota unavailable secret-test-token')
        with TemporaryDirectory() as folder,patch.dict('os.environ',{'HF_TOKEN':'secret-test-token'}):
            service=AudioService(folder,failing)
            job=service.start(sample(),'sanskrit');service.executor.shutdown(wait=True)
            result=service.status(job['id'])
            self.assertEqual(result['state'],'error')
            self.assertIn('quota unavailable',result['error'])
            self.assertNotIn('secret-test-token',result['error'])

    def test_api_serves_wav_and_validates_requests(self):
        with TemporaryDirectory() as folder:
            service=AudioService(folder,lambda text,path,source:write_test_wav(path))
            with patch.object(app,'audio_service',service):
                client=TestClient(app.app)
                self.assertEqual(set(client.get('/api/text-formats').json()['templates']),{'roman','sanskrit','kannada'})
                response=client.post('/api/audio',json={'text':sample(),'script':'sanskrit'})
                self.assertEqual(response.status_code,202)
                service.executor.shutdown(wait=True)
                job=client.get('/api/audio/'+response.json()['id']).json()
                audio=client.get(job['url'])
                self.assertEqual(audio.status_code,200)
                self.assertEqual(audio.headers['content-type'],'audio/wav')
                self.assertEqual(audio.content[:4],b'RIFF')
                self.assertEqual(client.get('/api/audio/not-a-hash/file').status_code,404)
                self.assertEqual(client.post('/api/audio',json={'text':'{missing}','script':'roman'}).status_code,422)
                self.assertEqual(client.post('/api/audio',json={'text':sample(),'script':'other'}).status_code,422)

    def test_vercel_audio_returns_recording_without_cache_or_background_jobs(self):
        with TemporaryDirectory() as folder:
            cache=Path(folder)/'must-not-be-created'
            destinations=[]
            def renderer(text,path,source):
                destinations.append(path)
                write_test_wav(path)
            service=AudioService(cache,renderer)
            with patch.object(app,'audio_service',service),patch.dict('os.environ',{'VERCEL':'1'}):
                response=TestClient(app.app).post('/api/audio',json={'text':sample(),'script':'sanskrit'})
            service.executor.shutdown(wait=True)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['cache-control'],'no-store')
            result=response.json()
            self.assertEqual(result['state'],'ready')
            self.assertTrue(result['url'].startswith('data:audio/wav;base64,'))
            self.assertEqual(base64.b64decode(result['url'].split(',',1)[1])[:4],b'RIFF')
            self.assertEqual(service.jobs,{})
            self.assertFalse(cache.exists())
            self.assertTrue(all(not path.exists() for path in destinations))

    def test_vercel_audio_rejects_oversized_recording_before_response_encoding(self):
        def oversized(text,path,source):
            with path.open('wb') as output:output.truncate(3_000_001)
        service=AudioService(renderer=oversized)
        result=service.generate_inline(sample(),'sanskrit')
        service.executor.shutdown(wait=True)
        self.assertEqual(result['state'],'error')
        self.assertIn('too large',result['error'])
        self.assertNotIn('url',result)

    def test_vercel_audio_provider_errors_are_redacted_before_truncation(self):
        secret='secret-test-token'
        def failing(*args):raise RuntimeError('x'*490+secret)
        service=AudioService(renderer=failing)
        with patch.dict('os.environ',{'HF_TOKEN':secret}):
            result=service.generate_inline(sample(),'sanskrit')
        service.executor.shutdown(wait=True)
        self.assertEqual(result['state'],'error')
        self.assertNotIn('secret-',result['error'])
        self.assertNotIn('url',result)


if __name__=='__main__':unittest.main()
