# ─────────────────────────────────────────────
# TEST — AI Brain (Gemini)
# Tests English + Arabic conversation
# ─────────────────────────────────────────────

from core.ai_brain import ai_brain

print("=" * 50)
print("TEST 1 — English Conversation")
print("=" * 50)

response = ai_brain.chat("Hello! Who are you?", language="en")
print(f"ARIA: {response}\n")

response = ai_brain.chat("What can you help me with?", language="en")
print(f"ARIA: {response}\n")

print("=" * 50)
print("TEST 2 — Arabic Conversation")
print("=" * 50)

ai_brain.reset_conversation()

response = ai_brain.chat("مرحباً، من أنت؟", language="ar")
print(f"ARIA: {response}\n")

response = ai_brain.chat("كيف يمكنك مساعدتي؟", language="ar")
print(f"ARIA: {response}\n")

print("AI Brain Test Complete! ✅")