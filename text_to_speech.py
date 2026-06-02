# ============================================================
#  text_to_speech.py  —  Text to Speech using pyttsx3
#  ElevenLabs free tier does not support library voices via API.
#  Using pyttsx3 (offline, free, works on all platforms).
#  For web: converts speech to WAV bytes for browser playback.
# ============================================================

import pyttsx3
import io
import wave
import tempfile
import os

def speak(text: str):
    """
    Speak text aloud using pyttsx3.
    Used by main.py (local desktop mode).
    """
    print(f"Assistant: {text}")
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[pyttsx3 Error] {e}")

def generate_audio_bytes(text: str) -> bytes | None:
    """
    Convert text to speech and return as WAV bytes.
    Used by app.py (web interface mode).
    Browser will play the WAV audio.
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)

        # Save to a temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        engine.stop()

        # Read bytes from temp file
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(tmp_path)

        if len(audio_bytes) > 100:
            print(f"[TTS] Generated {len(audio_bytes)} bytes of audio")
            return audio_bytes
        else:
            print("[TTS] Audio file too small — generation may have failed")
            return None

    except Exception as e:
        print(f"[TTS Error] {e}")
        return None
