"""
Voice Query Service for the Reporting module.

Provides speech-to-text and text-to-speech capabilities for
voice-based interaction with the analytics engine.

Pipeline:
    audio → STT (transcribe) → NLQ → report → TTS → response

Integration Points:
    - STT: External speech-to-text API (stub with clear integration point)
    - TTS: External text-to-speech API (stub with clear integration point)
    - NLQ: Internal Natural Language Query service

Usage:
    from apps.reporting.ai.voice_service import VoiceQueryService

    service = VoiceQueryService()

    # Full pipeline: voice in, voice + data out
    result = service.process_voice_query(
        org_id=org.id,
        audio_data=request.FILES['audio'].read(),
        user=request.user,
    )
    # result = {
    #     'text_query': 'What was my revenue last week?',
    #     'report_data': {...},
    #     'answer_text': 'Your revenue last week was ...',
    #     'audio_response_url': '/media/tts/abc123.mp3',
    #     'confidence': 0.85,
    # }

    # Individual operations
    text = service.transcribe(audio_data, language='tr')
    audio_bytes = service.text_to_speech("Hello world", language='tr')

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - Audio data is NOT stored permanently (privacy)
    - TTS responses are cached temporarily for playback
"""

import hashlib
import logging
import os
import tempfile
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Supported languages for STT/TTS
SUPPORTED_LANGUAGES = {
    'tr': 'Turkish',
    'en': 'English',
}

# Maximum audio file size (10 MB)
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024

# TTS cache directory (relative to MEDIA_ROOT)
TTS_CACHE_DIR = 'tts_cache'


class VoiceQueryService:
    """
    Service for voice-based analytics queries.

    Provides speech-to-text transcription, text-to-speech synthesis,
    and a full pipeline that combines both with the NLQ engine.
    """

    def __init__(self):
        self._nlq_service = None

    @property
    def nlq_service(self):
        """Lazy-load NLQ service."""
        if self._nlq_service is None:
            from apps.reporting.ai.nlq_service import NLQService
            self._nlq_service = NLQService()
        return self._nlq_service

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def transcribe(
        self,
        audio_data: bytes,
        language: str = 'tr',
    ) -> str:
        """
        Transcribe audio data to text using an external STT API.

        This is a stub implementation with a clear integration point
        for connecting to a real STT provider (Google Cloud Speech,
        Azure Speech, OpenAI Whisper, etc.).

        Args:
            audio_data: Raw audio bytes (WAV, MP3, WebM, etc.)
            language: Language code ('tr' for Turkish, 'en' for English)

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If audio data is empty or exceeds size limit
            RuntimeError: If STT service is not configured
        """
        if not audio_data:
            raise ValueError('Audio data is empty')

        if len(audio_data) > MAX_AUDIO_SIZE_BYTES:
            raise ValueError(
                f'Audio data exceeds maximum size of '
                f'{MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB'
            )

        if language not in SUPPORTED_LANGUAGES:
            logger.warning(
                'Unsupported language %s, falling back to Turkish', language,
            )
            language = 'tr'

        # ─── INTEGRATION POINT: STT Provider ───
        # Replace this stub with your preferred STT provider.
        #
        # Example integrations:
        #
        # --- OpenAI Whisper ---
        # from openai import OpenAI
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
        #     f.write(audio_data)
        #     f.flush()
        #     transcript = client.audio.transcriptions.create(
        #         model="whisper-1",
        #         file=open(f.name, 'rb'),
        #         language=language,
        #     )
        #     return transcript.text
        #
        # --- Google Cloud Speech ---
        # from google.cloud import speech
        # client = speech.SpeechClient()
        # audio = speech.RecognitionAudio(content=audio_data)
        # config = speech.RecognitionConfig(
        #     language_code=f'{language}-{language.upper()}',
        #     enable_automatic_punctuation=True,
        # )
        # response = client.recognize(config=config, audio=audio)
        # return ' '.join(r.alternatives[0].transcript for r in response.results)

        stt_provider = self._get_stt_provider()

        if stt_provider == 'openai':
            return self._transcribe_openai(audio_data, language)
        elif stt_provider == 'google':
            return self._transcribe_google(audio_data, language)
        else:
            logger.warning(
                'No STT provider configured. Set VOICE_STT_PROVIDER in settings.'
            )
            raise RuntimeError(
                'Speech-to-text service is not configured. '
                'Set VOICE_STT_PROVIDER in Django settings.'
            )

    def text_to_speech(
        self,
        text: str,
        language: str = 'tr',
    ) -> bytes:
        """
        Convert text to speech audio using an external TTS API.

        This is a stub implementation with a clear integration point
        for connecting to a real TTS provider.

        Args:
            text: Text to convert to speech
            language: Language code ('tr' for Turkish, 'en' for English)

        Returns:
            bytes: Audio data (MP3 format)

        Raises:
            ValueError: If text is empty
            RuntimeError: If TTS service is not configured
        """
        if not text or not text.strip():
            raise ValueError('Text is empty')

        if language not in SUPPORTED_LANGUAGES:
            language = 'tr'

        # ─── INTEGRATION POINT: TTS Provider ───
        # Replace this stub with your preferred TTS provider.
        #
        # Example integrations:
        #
        # --- OpenAI TTS ---
        # from openai import OpenAI
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # response = client.audio.speech.create(
        #     model="tts-1",
        #     voice="alloy",
        #     input=text,
        # )
        # return response.content
        #
        # --- Google Cloud TTS ---
        # from google.cloud import texttospeech
        # client = texttospeech.TextToSpeechClient()
        # input_text = texttospeech.SynthesisInput(text=text)
        # voice = texttospeech.VoiceSelectionParams(
        #     language_code=f'{language}-{language.upper()}',
        # )
        # config = texttospeech.AudioConfig(
        #     audio_encoding=texttospeech.AudioEncoding.MP3,
        # )
        # response = client.synthesize_speech(
        #     input=input_text, voice=voice, audio_config=config,
        # )
        # return response.audio_content

        tts_provider = self._get_tts_provider()

        if tts_provider == 'openai':
            return self._tts_openai(text, language)
        elif tts_provider == 'google':
            return self._tts_google(text, language)
        else:
            logger.warning(
                'No TTS provider configured. Set VOICE_TTS_PROVIDER in settings.'
            )
            raise RuntimeError(
                'Text-to-speech service is not configured. '
                'Set VOICE_TTS_PROVIDER in Django settings.'
            )

    def process_voice_query(
        self,
        org_id,
        audio_data: bytes,
        user=None,
        language: str = 'tr',
    ) -> Dict[str, Any]:
        """
        Full voice query pipeline: audio -> STT -> NLQ -> report -> TTS.

        Args:
            org_id: Organization UUID (multi-tenant isolation)
            audio_data: Raw audio bytes from the user
            user: User making the query
            language: Language code

        Returns:
            dict with keys:
                - text_query (str): Transcribed text from audio
                - report_data (dict|list|None): Report/query result data
                - answer_text (str): Natural language answer
                - audio_response_url (str|None): URL to TTS audio response
                - visualization_hint (str): Suggested chart type
                - confidence (float): Confidence in the interpretation
        """
        # Step 1: Transcribe audio to text
        try:
            text_query = self.transcribe(audio_data, language)
        except (ValueError, RuntimeError) as exc:
            logger.error(
                'STT transcription failed: org=%s error=%s', org_id, exc,
            )
            return {
                'text_query': '',
                'report_data': None,
                'answer_text': str(exc),
                'audio_response_url': None,
                'visualization_hint': 'text',
                'confidence': 0.0,
            }

        if not text_query or not text_query.strip():
            return {
                'text_query': '',
                'report_data': None,
                'answer_text': 'Could not understand the audio. Please try again.',
                'audio_response_url': None,
                'visualization_hint': 'text',
                'confidence': 0.0,
            }

        logger.info(
            'Voice query transcribed: org=%s text=%r',
            org_id, text_query[:80],
        )

        # Step 2: Process through NLQ
        try:
            nlq_result = self.nlq_service.process_query(
                org_id=org_id,
                question=text_query,
                user=user,
            )
        except Exception as exc:
            logger.error(
                'NLQ processing failed for voice query: org=%s error=%s',
                org_id, exc,
            )
            nlq_result = {
                'answer': 'An error occurred while processing your question.',
                'data': None,
                'visualization_hint': 'text',
                'confidence': 0.0,
            }

        answer_text = nlq_result.get('answer', '')

        # Step 3: Convert answer to speech (optional, non-blocking)
        audio_response_url = None
        try:
            audio_bytes = self.text_to_speech(answer_text, language)
            audio_response_url = self._save_tts_audio(audio_bytes, org_id)
        except (RuntimeError, ValueError) as exc:
            logger.info(
                'TTS generation skipped (not configured or failed): %s', exc,
            )
        except Exception as exc:
            logger.warning(
                'TTS generation failed unexpectedly: %s', exc,
            )

        return {
            'text_query': text_query,
            'report_data': nlq_result.get('data'),
            'answer_text': answer_text,
            'audio_response_url': audio_response_url,
            'visualization_hint': nlq_result.get('visualization_hint', 'text'),
            'confidence': nlq_result.get('confidence', 0.0),
        }

    # ─────────────────────────────────────────────────────────
    # PROVIDER CONFIGURATION
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_stt_provider() -> str:
        """Get configured STT provider name from settings."""
        return getattr(settings, 'VOICE_STT_PROVIDER', '')

    @staticmethod
    def _get_tts_provider() -> str:
        """Get configured TTS provider name from settings."""
        return getattr(settings, 'VOICE_TTS_PROVIDER', '')

    # ─────────────────────────────────────────────────────────
    # STT PROVIDER IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _transcribe_openai(audio_data: bytes, language: str) -> str:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes
            language: Language code

        Returns:
            str: Transcribed text
        """
        try:
            import openai
        except ImportError:
            raise RuntimeError('openai package is required for Whisper STT')

        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY is not configured')

        client = openai.OpenAI(api_key=api_key)

        # Write audio to temporary file for the API
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model='whisper-1',
                    file=audio_file,
                    language=language,
                )
            return transcript.text.strip()
        finally:
            os.unlink(tmp_path)

    @staticmethod
    def _transcribe_google(audio_data: bytes, language: str) -> str:
        """
        Transcribe audio using Google Cloud Speech-to-Text.

        Args:
            audio_data: Raw audio bytes
            language: Language code

        Returns:
            str: Transcribed text
        """
        try:
            from google.cloud import speech
        except ImportError:
            raise RuntimeError(
                'google-cloud-speech package is required for Google STT'
            )

        language_codes = {
            'tr': 'tr-TR',
            'en': 'en-US',
        }

        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            language_code=language_codes.get(language, 'tr-TR'),
            enable_automatic_punctuation=True,
        )

        response = client.recognize(config=config, audio=audio)
        return ' '.join(
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        ).strip()

    # ─────────────────────────────────────────────────────────
    # TTS PROVIDER IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _tts_openai(text: str, language: str) -> bytes:
        """
        Generate speech using OpenAI TTS API.

        Args:
            text: Text to convert
            language: Language code

        Returns:
            bytes: MP3 audio data
        """
        try:
            import openai
        except ImportError:
            raise RuntimeError('openai package is required for OpenAI TTS')

        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY is not configured')

        client = openai.OpenAI(api_key=api_key)

        response = client.audio.speech.create(
            model='tts-1',
            voice='alloy',
            input=text[:4096],  # TTS character limit
        )
        return response.content

    @staticmethod
    def _tts_google(text: str, language: str) -> bytes:
        """
        Generate speech using Google Cloud Text-to-Speech.

        Args:
            text: Text to convert
            language: Language code

        Returns:
            bytes: MP3 audio data
        """
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise RuntimeError(
                'google-cloud-texttospeech package is required for Google TTS'
            )

        language_codes = {
            'tr': 'tr-TR',
            'en': 'en-US',
        }

        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=text[:5000])
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_codes.get(language, 'tr-TR'),
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )

        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config,
        )
        return response.audio_content

    # ─────────────────────────────────────────────────────────
    # TTS AUDIO CACHING
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _save_tts_audio(audio_bytes: bytes, org_id) -> Optional[str]:
        """
        Save TTS audio to a temporary file and return its URL.

        Args:
            audio_bytes: MP3 audio data
            org_id: Organization UUID (for path namespacing)

        Returns:
            str: URL to the audio file, or None if save fails
        """
        if not audio_bytes:
            return None

        media_root = getattr(settings, 'MEDIA_ROOT', '/tmp')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')

        cache_dir = os.path.join(media_root, TTS_CACHE_DIR, str(org_id))
        os.makedirs(cache_dir, exist_ok=True)

        # Generate unique filename from content hash
        content_hash = hashlib.md5(audio_bytes).hexdigest()[:12]
        filename = f'tts_{content_hash}.mp3'
        filepath = os.path.join(cache_dir, filename)

        try:
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)

            url = f'{media_url}{TTS_CACHE_DIR}/{org_id}/{filename}'
            return url
        except OSError as exc:
            logger.error('Failed to save TTS audio: %s', exc)
            return None
