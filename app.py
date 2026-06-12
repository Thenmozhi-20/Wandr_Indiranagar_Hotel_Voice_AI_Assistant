# ============================================================
#  app.py  —  Flask Web Application
# ============================================================

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)

print("⏳ Starting Wandr Hotels Assistant...")

from speech_to_text import convert_from_base64
from response_generator import get_ai_response, reset_conversation
from text_to_speech import generate_audio_bytes
from sheets_logger import log_chat
from config import FLASK_SECRET_KEY

app.secret_key = FLASK_SECRET_KEY

print("=" * 50)
print("  🏨 Wandr Indiranagar — Voice Assistant")
print("  Open: http://127.0.0.1:5000")
print("=" * 50)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask/text", methods=["POST"])
def ask_text():
    data      = request.get_json()
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    reply       = get_ai_response(user_text)
    audio_bytes = generate_audio_bytes(reply)
    audio_b64   = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    # ── Log to Google Sheets ──────────────────────────────────
    log_chat(user_text, reply, mode="text")

    return jsonify({"reply": reply, "audio": audio_b64})


@app.route("/ask/voice", methods=["POST"])
def ask_voice():
    data      = request.get_json()
    audio_b64 = data.get("audio", "")
    if not audio_b64:
        return jsonify({"error": "No audio provided"}), 400

    user_text = convert_from_base64(audio_b64)
    print(f"[Voice] Transcript: {user_text}")

    if not user_text or user_text == "no speech":
        return jsonify({
            "reply": "I did not catch that. Could you please repeat?",
            "transcript": "",
            "audio": None
        })

    reply = get_ai_response(user_text)
    print(f"[Voice] Reply: {reply}")

    audio_bytes = generate_audio_bytes(reply)
    audio_out   = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    # ── Log to Google Sheets ──────────────────────────────────
    log_chat(user_text, reply, mode="voice")

    return jsonify({"transcript": user_text, "reply": reply, "audio": audio_out})


@app.route("/reset", methods=["POST"])
def reset():
    reset_conversation()
    return jsonify({"status": "reset"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
