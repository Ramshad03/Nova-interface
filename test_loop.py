# ─────────────────────────────────────────────
# TEST — Full Interaction Loop
# Console test without UI
# Say "Hey Alexa" to trigger
# ─────────────────────────────────────────────

import time
from core.interaction_loop import interaction_loop

# ─── Connect console callbacks ────────────────
def on_state(state):
    print(f"[STATE] → {state.upper()}")

def on_subtitle(text, speaker):
    print(f"[{speaker}]: {text}")

def on_clear():
    print("[SUBTITLE CLEARED]")

def on_lang(lang):
    print(f"[LANGUAGE] → {lang.upper()}")

interaction_loop.on_state_change    = on_state
interaction_loop.on_subtitle        = on_subtitle
interaction_loop.on_clear_subtitle  = on_clear
interaction_loop.on_language_change = on_lang

# ─── Start loop ───────────────────────────────
print("Starting Alexa interaction loop...")
print('Say "Hey Alexa" to begin!\n')
print("(Press Ctrl+C to stop)\n")

interaction_loop.start()

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    interaction_loop.stop()
    print("\nStopped.")