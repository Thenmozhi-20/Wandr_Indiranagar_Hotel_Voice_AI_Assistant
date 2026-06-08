from groq import Groq
from config import GROQ_API_KEY
import base64, tempfile, os

client = Groq(api_key=GROQ_API_KEY)

def convert_from_base64(audio_base64: str) -> str:
    try:
        audio_bytes = base64.b64decode(audio_base64)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=("audio.webm", f),
                model="whisper-large-v3",
                language="en"
            )
        os.unlink(tmp_path)
        return transcription.text.strip() or "no speech"
    except Exception as e:
        print(f"[Groq Whisper Error] {e}")
        return "no speech"