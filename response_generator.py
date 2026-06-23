# ============================================================
#  response_generator.py  —  Wandr Hotels AI Brain
#  JSON knowledge base + Groq LLaMA 3
# ============================================================

from groq import Groq
from knowledge_base import get_relevant_context
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


def get_ai_response(user_text: str) -> str:
    global chat_history
    user_lower = user_text.lower()

    # ── Booking shortcut ──────────────────────────────────────
    if any(t in user_lower for t in BOOKING_TRIGGERS):
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": BOOKING_REPLY})
        return BOOKING_REPLY

    try:
        # ── Force rooms context for room type questions ───────
        if any(t in user_lower for t in ROOM_TYPE_TRIGGERS):
            context = get_relevant_context("room types pricing", top_k=3)
        else:
            context = get_relevant_context(user_text, top_k=3)

        # Build system prompt with context
        system = SYSTEM_PROMPT.format(context=context)

        # Only pass last 4 messages of history
        messages = [{"role": "system", "content": system}]
        for msg in chat_history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_text})

        # Call Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=120,
            temperature=0.0,
            top_p=0.7
        )

        reply = response.choices[0].message.content.strip()

        # Block hallucinated content
        if any(t in reply.lower() for t in HALLUCINATION_TRIGGERS):
            print(f"[HALLUCINATION BLOCKED]: {reply}")
            reply = "I don't have that information — please contact our front desk directly."

        # Save to history
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply})
        if len(chat_history) > 6:
            chat_history = chat_history[-6:]

        print(f"[Reply] {reply}")
        return reply

    except Exception as e:
        print(f"[Groq Error] {e}")
        return (
            "I'm having a little trouble right now. "
            "Please contact our front desk or visit wandrhotels.com."
        )


def reset_conversation():
    global chat_history
    chat_history = []
    print("[Conversation reset]")
