# ============================================================
#  record_audio.py  —  Local Microphone Recording
#  Used by main.py (desktop mode only).
#  Records audio from mic and saves as voice.wav
# ============================================================

import sounddevice as sd
import soundfile as sf
import numpy as np

SAMPLE_RATE  = 16000   # 16kHz — Whisper prefers this
DURATION_SEC = 5       # seconds to record
OUTPUT_FILE  = "voice.wav"


def record(duration: int = DURATION_SEC, filename: str = OUTPUT_FILE):
    """
    Record audio from default microphone and save as WAV.
    Press Enter to stop early (blocking mode).
    """
    print(f"\n🎙  Recording for {duration} seconds... Speak now!")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()  # wait until recording is done
    sf.write(filename, audio, SAMPLE_RATE)
    print(f"✓  Saved to {filename}")
