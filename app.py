# ============================================================
#  app.py  —  Flask Web Application
# ============================================================

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64
import os

app = Flask(__name__)
CORS(app)

print("⏳ Starting Wandr Hotels Assistant...")

from speech_to_text import convert_from_base64
from response_generator import get_ai_response, reset_conversation
from text_to_speech import generate_audio_bytes
from sheets_logger import log_chat
from admin_updater import (
    add_faq, update_room_price, update_room_availability,
    add_nearby_place, update_food_info, add_policy, update_checkin_time,
    delete_faq, delete_nearby_place, delete_policy, get_current_data
)
from config import FLASK_SECRET_KEY

app.secret_key = FLASK_SECRET_KEY
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "wandr@admin")

print("=" * 50)
print("  🏨 Wandr Indiranagar — Voice Assistant")
print("  Open: http://127.0.0.1:5000")
print("=" * 50)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route("/admin/data", methods=["GET"])
def admin_data():
    """Returns current FAQs, nearby places, and policies for the delete UI."""
    try:
        data = get_current_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[Admin Data Error] {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/admin/update", methods=["POST"])
def admin_update():
    data   = request.get_json()
    action = data.get("action")
    try:
        if action == "add_faq":
            msg = add_faq(data["question"], data["answer"])
        elif action == "update_room_price":
            msg = update_room_price(data["room_type"], data["plan"], data["new_price"])
        elif action == "update_room_availability":
            msg = update_room_availability(data["room_type"], data["status"])
        elif action == "update_food":
            msg = update_food_info(data["field"], data["value"])
        elif action == "add_nearby":
            msg = add_nearby_place(data["name"], data["distance"], data["category"])
        elif action == "add_policy":
            msg = add_policy(data["policy"])
        elif action == "update_checkin":
            msg = update_checkin_time(data["checkin"], data["checkout"])
        elif action == "delete_faq":
            msg = delete_faq(int(data["index"]))
        elif action == "delete_nearby":
            msg = delete_nearby_place(int(data["index"]))
        elif action == "delete_policy":
            msg = delete_policy(int(data["index"]))
        else:
            return jsonify({"success": False, "error": "Unknown action"})
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Admin Error] {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/ask/text", methods=["POST"])
def ask_text():
    data      = request.get_json()
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    reply       = get_ai_response(user_text)
    audio_bytes = generate_audio_bytes(reply)
    audio_b64   = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
    log_chat(user_text, reply)
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

    reply       = get_ai_response(user_text)
    audio_bytes = generate_audio_bytes(reply)
    audio_out   = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
    log_chat(user_text, reply)
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
