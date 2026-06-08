from gtts import gTTS
import io

def generate_audio_bytes(text: str) -> bytes | None:
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"[gTTS Error] {e}")
        return None