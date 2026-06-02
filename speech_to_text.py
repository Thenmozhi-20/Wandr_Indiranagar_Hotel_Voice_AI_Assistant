# ============================================================
#  speech_to_text.py  —  Whisper Speech-to-Text
#  Fixed: browser sends WebM audio, we now handle it correctly.
# ============================================================

import whisper
import base64
import tempfile
import os
from config import WHISPER_MODEL

# Load model once at startup
print(f"[Whisper] Loading '{WHISPER_MODEL}' model...")
model = whisper.load_model(WHISPER_MODEL)
print("[Whisper] Model ready.")

def convert(audio_path: str = "voice.wav") -> str:
    """
    Convert a WAV file to text using Whisper.
    Used by main.py (local mic mode).
    """
    try:
        print("[Whisper] Converting speech to text...")
        result = model.transcribe(audio_path, language="en", fp16=False)
        text = result["text"].strip()
        return text if text else "no speech"
    except Exception as e:
        print(f"[Whisper Error] {e}")
        return "no speech"

def convert_from_base64(audio_base64: str) -> str:
    """
    Convert base64 audio from browser to text.
    Browser sends WebM format — we save with .webm extension
    so Whisper/ffmpeg can read it correctly.
    """
    try:
        audio_bytes = base64.b64decode(audio_base64)

        if len(audio_bytes) < 100:
            print("[Whisper] Audio too short — no speech detected")
            return "no speech"

        # Save as .webm (browser records in WebM format)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        print(f"[Whisper] Transcribing {len(audio_bytes)} bytes of audio...")
        result = model.transcribe(tmp_path, language="en", fp16=False)
        text = result["text"].strip()

        os.unlink(tmp_path)

        print(f"[Voice] Transcript: {text}")
        return text if text else "no speech"

    except Exception as e:
        print(f"[Whisper base64 Error] {e}")
        return "no speech"
