# ============================================================
#  main.py  —  Local Desktop Voice Assistant
#  No RAG, No ChromaDB. Direct JSON-based assistant.
#  Use this when running on your own computer with a mic.
#  For web access, run app.py instead.
# ============================================================

from record_audio import record
from speech_to_text import convert
from text_to_speech import speak
from response_generator import get_ai_response, reset_conversation


def main():
    print("=" * 55)
    print("   🏨 Wandr Indiranagar — Voice Assistant (Local)")
    print("=" * 55)
    print("  Say 'goodbye' or 'bye' to exit.\n")

    speak("Welcome to Wandr Indiranagar, Bangalore. How may I assist you today?")

    while True:
        try:
            # Step 1: Record voice
            record()

            # Step 2: Convert to text
            user_text = convert().strip().lower()
            print(f"\n[You said]: {user_text}\n")

            if not user_text or user_text == "no speech":
                speak("I did not catch that. Could you please repeat?")
                continue

            # Step 3: Check for exit
            if any(w in user_text for w in ["goodbye", "bye", "exit", "quit", "stop"]):
                speak("Thank you for choosing Wandr Indiranagar. Have a wonderful day!")
                break

            # Step 4: Get AI reply
            print("[Thinking...]")
            reply = get_ai_response(user_text)
            print(f"[Assistant]: {reply}\n")

            # Step 5: Speak reply
            speak(reply)

        except KeyboardInterrupt:
            print("\n[Interrupted]")
            speak("Goodbye. Thank you for visiting Wandr Indiranagar.")
            break
        except Exception as e:
            print(f"[Error]: {e}")
            speak("Something went wrong. Please try again.")


if __name__ == "__main__":
    main()
