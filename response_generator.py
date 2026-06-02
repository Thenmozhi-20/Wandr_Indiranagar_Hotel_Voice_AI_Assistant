# ============================================================
#  response_generator.py  —  Wandr Hotels AI Brain
#  ChromaDB-powered knowledge base + Groq LLaMA 3
#  Fixed: strict hallucination prevention
# ============================================================

from groq import Groq
from knowledge_base import get_relevant_context
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# ── Conversation history ──────────────────────────────────────
chat_history = []

# ── System prompt — strict grounding ─────────────────────────
SYSTEM_PROMPT = """
You are Maya, the front desk assistant for Wandr Indiranagar, Bangalore.

STRICT RULES — FOLLOW EXACTLY:

1. Answer ONLY using facts from the HOTEL CONTEXT below.
2. If something is NOT in the context, say exactly:
   "I don't have that information — please contact our front desk directly."
3. NEVER guess, assume, or use your own knowledge to fill gaps.
4. NEVER mention payment methods like UPI, GPay, PhonePe, Paytm, or net banking
   — the hotel only accepts what is listed in the context.
5. NEVER mention malls, restaurants, or places NOT listed in the context.
6. NEVER offer to generate QR codes, process payments, or confirm bookings
   — you only provide information, not transactions.
7. If context says the gym/fitness center is NOT available, say:
   "No, we do not have a gym or fitness center at this property."
8. If context says the swimming pool is NOT available, say:
   "No, we do not have a swimming pool at this property."
9. For nearby restaurants, use ONLY the restaurants listed in the context
   under nearby restaurants. Do NOT use nearby places/landmarks as restaurants.
10. Keep replies to 2-3 sentences. Be warm and direct.
11. Never use bullet points or markdown formatting.
12. For dinner/lunch questions: check if the hotel restaurant serves those meals
    from the context before answering.

HOTEL CONTEXT:
{context}
"""

# ── Known hallucination triggers ──────────────────────────────
HALLUCINATION_TRIGGERS = [
    "gpay", "google pay", "phonepay", "phonepe", "paytm",
    "net banking", "upi", "qr code", "qr-code",
    "forum mall", "garuda mall", "orion mall",
    "i'll generate", "i will generate",
    "booking confirmed", "reservation confirmed",
    "i'll book", "i will book",
    "i'll process", "i will process"
]


def get_ai_response(user_text: str) -> str:
    """
    Takes user question → ChromaDB semantic search →
    Groq LLaMA 3 generates grounded reply.
    """
    global chat_history

    try:
        # Step 1: Semantic search on ChromaDB
        context = get_relevant_context(user_text, top_k=6)
        print(f"[KB] Context length: {len(context)} chars")

        # Step 2: Build conversation history
        history_str = ""
        for msg in chat_history[-6:]:
            role = "Guest" if msg["role"] == "user" else "Maya"
            history_str += f"{role}: {msg['content']}\n"

        # Step 3: Build full system prompt
        system = SYSTEM_PROMPT.format(context=context)
        if history_str:
            system += f"\nCONVERSATION SO FAR:\n{history_str}"

        # Step 4: Save user message to history
        chat_history.append({"role": "user", "content": user_text})

        # Step 5: Call Groq LLaMA with very low temperature
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_text}
            ],
            max_tokens=150,
            temperature=0.1,   # Very low = minimal hallucination
            top_p=0.8
        )

        reply = response.choices[0].message.content.strip()

        # Step 6: Post-processing — block hallucinated content
        if any(trigger in reply.lower() for trigger in HALLUCINATION_TRIGGERS):
            print(f"[HALLUCINATION BLOCKED] Fabricated content detected in reply.")
            reply = (
                "For payment or booking assistance, please contact our "
                "front desk directly or visit wandrhotels.com."
            )

        # Step 7: Save reply to history
        chat_history.append({"role": "assistant", "content": reply})

        # Keep only last 10 messages
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]

        print(f"[Reply] {reply}\n")
        return reply

    except Exception as e:
        print(f"[Groq Error] {e}")
        return (
            "I'm having a little trouble right now. "
            "Please contact our front desk or visit wandrhotels.com for assistance."
        )


def reset_conversation():
    """Reset conversation for a fresh start."""
    global chat_history
    chat_history = []
    print("[Conversation reset]")
