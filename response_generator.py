# ============================================================
#  response_generator.py  —  Wandr Hotels AI Brain
#  JSON knowledge base + Groq LLaMA 3
# ============================================================

from groq import Groq
from knowledge_base import (
    get_relevant_context, get_direct_answer,
    get_price_answer, get_room_types_answer
)
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# ── Conversation history ──────────────────────────────────────
chat_history = []

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are Maya, the front desk assistant for Wandr Indiranagar, Bangalore.

STRICT RULES — FOLLOW EXACTLY:

1. Answer ONLY using facts from the HOTEL CONTEXT below. No exceptions.
2. The HOTEL CONTEXT always contains room types. If the guest asks about room types,
   list them from the context. ALWAYS look for "ROOM TYPES" section in the context.
3. If the answer is NOT in the context, say EXACTLY:
   "I don't have that information — please contact our front desk directly."
4. NEVER use your own knowledge. NEVER guess. NEVER assume.
5. NEVER invent nearby places, hospitals, bus stands, or restaurants
   not listed in the context.
6. NEVER mention honeymoon packages, complimentary upgrades, candlelit dinners,
   or special packages unless explicitly in the context.
7. Keep every reply to 1-2 short sentences only. No exceptions.
8. Never use bullet points or lists. Plain sentences only.
9. Be warm but very brief and direct.
10. For booking requests → say: "We'd love to host you! Please call our front desk
    or visit wandrhotels.com to complete your booking."
11. For celebrations/events → only mention what is explicitly in the context.
12. When the context has a "NEARBY PLACES LIST", and the guest asks what places are nearby,
    mention ALL items from that list, not just some. Keep it to one flowing sentence.
13. For price questions, quote the exact rupee price from the ROOM TYPES or PRICING
    section, with the plan (room only / with breakfast). Prices are plus taxes, for
    2 guests. Rooms marked Sold Out cannot be booked. We cannot check prices for
    specific dates; for that, say to visit wandrhotels.com.

HOTEL CONTEXT:
{context}
"""

# ── Hallucination triggers ────────────────────────────────────
HALLUCINATION_TRIGGERS = [
    "gpay", "google pay", "phonepay", "phonepe", "paytm",
    "net banking", "qr code", "qr-code",
    "forum mall", "garuda mall", "orion mall",
    "i'll generate", "i will generate",
    "booking confirmed", "reservation confirmed",
    "i'll book", "i will book",
    "candlelit dinner", "bouquet of flowers",
    "complimentary upgrade", "honeymoon package",
    "special package", "romantic package",
]

# ── Booking intent shortcuts ──────────────────────────────────
# NOTE: Only exact booking phrases — do NOT include "room" alone
BOOKING_TRIGGERS = [
    "book a room", "make a reservation", "reserve a room",
    "want to book", "i want to stay", "how do i book",
    "can i book", "book room"
]

# ── Room type intent shortcut — always answer from KB ─────────
ROOM_TYPE_TRIGGERS = [
    "types of room", "room types", "type of room",
    "what rooms", "rooms available", "room available",
    "types rooms", "room options", "kind of room",
    "kinds of room", "what type", "available rooms"
]

BOOKING_REPLY = (
    "We'd love to host you at Wandr Indiranagar! "
    "Please call our front desk or visit wandrhotels.com to complete your booking."
)


def _remember(user_text: str, reply: str):
    global chat_history
    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": reply})
    chat_history = chat_history[-6:]


def get_ai_response(user_text: str) -> str:
    global chat_history
    user_lower = user_text.lower()
    prev_user  = next((m["content"] for m in reversed(chat_history)
                       if m["role"] == "user"), "")

    # 1. Facts answered straight from the JSON (police, payment, facilities...)
    reply = get_direct_answer(user_text)
    if reply:
        _remember(user_text, reply)
        return reply

    # 2. Room price questions -> exact prices from the JSON
    reply = get_price_answer(user_text, prev_user)
    if reply:
        _remember(user_text, reply)
        return reply

    # 3. Room type questions -> room list from the JSON
    if any(t in user_lower for t in ROOM_TYPE_TRIGGERS):
        reply = get_room_types_answer()
        _remember(user_text, reply)
        return reply

    # 4. Plain booking request
    if any(t in user_lower for t in BOOKING_TRIGGERS):
        _remember(user_text, BOOKING_REPLY)
        return BOOKING_REPLY

    # 5. Everything else -> AI using the retrieved context
    try:
        context = get_relevant_context(f"{prev_user} {user_text}", top_k=3)

        # Build system prompt with context
        system = SYSTEM_PROMPT.format(context=context)

        # Only pass last 4 messages of history
        messages = [{"role": "system", "content": system}]
        for msg in chat_history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_text})

        # Call Groq
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            max_tokens=400,
            temperature=0.0,
            reasoning_effort="low"
        )

        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            reply = "I don't have that information — please contact our front desk directly."

        # Block hallucinated content
        if any(t in reply.lower() for t in HALLUCINATION_TRIGGERS):
            print(f"[HALLUCINATION BLOCKED]: {reply}")
            reply = "I don't have that information — please contact our front desk directly."

        # Save to history
        _remember(user_text, reply)

        print(f"[Reply] {reply}")
        return reply

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Groq Error] {e}")
        return (
            "I'm having a little trouble right now. "
            "Please contact our front desk or visit wandrhotels.com."
        )


def reset_conversation():
    global chat_history
    chat_history = []
    print("[Conversation reset]")
