# ─────────────────────────────────────────────
# INTERACTION LOOP — Full Voice Pipeline
# Always-on classroom mode
# Detects voice → AI → Speaks → Repeats
# ─────────────────────────────────────────────

import threading
import time
from core.stt_engine import stt
from core.tts_engine import tts
from core.ai_brain import ai_brain
from config.config_manager import config


# ─────────────────────────────────────────────
# INTERACTION LOOP CLASS
# ─────────────────────────────────────────────
class InteractionLoop:

    STATE_IDLE      = "idle"
    STATE_LISTENING = "listening"
    STATE_THINKING  = "thinking"
    STATE_SPEAKING  = "speaking"

    def __init__(self):
        self.current_state  = self.STATE_IDLE
        self.current_language = "en"
        self.is_running     = False
        self._loop_thread   = None

        # ─── UI Callbacks ─────────────────────
        self.on_state_change    = None
        self.on_subtitle        = None
        self.on_clear_subtitle  = None
        self.on_language_change = None

    # ─────────────────────────────────────────
    # START
    # ─────────────────────────────────────────
    def start(self):
        """Start always-on interaction loop."""
        if self.is_running:
            print("[LOOP] Already running — skipping")
            return

        self.is_running = True
        print("[LOOP] Starting interaction loop ✅")

        # ─── Startup greeting ─────────────────
        self._speak_startup_greeting()

        # ─── Start loop thread ────────────────
        self._loop_thread = threading.Thread(
            target=self._always_on_loop,
            daemon=True
        )
        self._loop_thread.start()

    # ─── Stop ─────────────────────────────────
    def stop(self):
        """Stop interaction loop."""
        self.is_running = False
        stt.stop()
        tts.stop()
        print("[LOOP] Stopped.")

    # ─── Pause (dashboard open) ───────────────
    def pause(self):
        """Pause loop when dashboard opens."""
        self.is_running = False
        stt.stop()
        tts.stop()
        print("[LOOP] Paused ⏸")

    # ─── Resume (dashboard close) ─────────────
    def resume(self):
        """Resume loop when dashboard closes."""
        if self.is_running:
            return

        self.is_running = True
        print("[LOOP] Resuming ▶")

        self._loop_thread = threading.Thread(
            target=self._always_on_loop,
            daemon=True
        )
        self._loop_thread.start()

    # ─────────────────────────────────────────
    # ALWAYS-ON LOOP
    # ─────────────────────────────────────────
    def _always_on_loop(self):
        """
        Main loop:
        1. Listen for voice
        2. Transcribe
        3. Get AI response
        4. Speak response
        5. Repeat
        """
        print("[LOOP] Always-on loop running 🎤")

        while self.is_running:
            try:
                # ─── Set listening state ──────
                self._set_state(self.STATE_LISTENING)
                self._clear_subtitle()

                # ─── Listen for voice ─────────
                result = stt.listen(duration=6)

                # ─── Check if paused ──────────
                if not self.is_running:
                    break

                user_text     = result.get("text", "").strip()
                detected_lang = result.get("language", "en")

                # ─── Skip empty/short results ─
                if not user_text or len(user_text) < 2:
                    self._set_state(self.STATE_IDLE)
                    time.sleep(0.3)
                    continue

                # ─── Update language ──────────
                self.current_language = detected_lang
                self._emit_language(detected_lang)
                self._emit_subtitle(user_text, "YOU")
                print(f"[LOOP] 🎤 ({detected_lang}): {user_text}")

                # ─── Get AI response ──────────
                self._set_state(self.STATE_THINKING)
                if detected_lang == "ar":
                    self._emit_subtitle("جاري التفكير...", "ALEXA")
                else:
                    self._emit_subtitle("Thinking...", "ALEXA")

                response = ai_brain.chat(
                    user_text, language=detected_lang
                )

                # ─── Check if paused ──────────
                if not self.is_running:
                    break

                # ─── Speak response ───────────
                self._set_state(self.STATE_SPEAKING)
                robot_name = config.get("robot", "name", default="Alexa")
                self._emit_subtitle(response, robot_name.upper())
                print(f"[LOOP] 🔊 {robot_name}: {response[:80]}...")

                tts.speak(response, language=detected_lang)

                # Wait for speech to finish
                while tts.is_speaking and self.is_running:
                    time.sleep(0.1)

                # ─── Brief pause then loop ────
                self._set_state(self.STATE_IDLE)
                self._clear_subtitle()
                ai_brain.reset_conversation()
                time.sleep(0.5)

            except Exception as e:
                print(f"[LOOP ERROR] {e}")
                self._set_state(self.STATE_IDLE)
                time.sleep(1)

        print("[LOOP] Loop exited.")

    # ─────────────────────────────────────────
    # STARTUP GREETING
    # ─────────────────────────────────────────
    def _speak_startup_greeting(self):
        """Speak greeting when app starts — uses live config."""
        # Reload config to get latest saved dashboard values
        from config.config_manager import ConfigManager
        fresh = ConfigManager()
        robot_name = fresh.robot_name

        greeting = (
            f"Hello! I am {robot_name}, your school assistant. "
            f"I am here to help you with any questions you have. "
            f"Please go ahead and ask me anything!"
        )
        self._set_state(self.STATE_SPEAKING)
        self._emit_subtitle(greeting, robot_name.upper())
        tts.speak(greeting, language="en")

        while tts.is_speaking:
            time.sleep(0.1)

        self._set_state(self.STATE_IDLE)
        self._clear_subtitle()

    # ─────────────────────────────────────────
    # UI HELPERS
    # ─────────────────────────────────────────
    def _set_state(self, state: str):
        self.current_state = state
        if self.on_state_change:
            self.on_state_change(state)

    def _emit_subtitle(self, text: str, speaker: str):
        if self.on_subtitle:
            self.on_subtitle(text, speaker)

    def _clear_subtitle(self):
        if self.on_clear_subtitle:
            self.on_clear_subtitle()

    def _emit_language(self, lang: str):
        if self.on_language_change:
            self.on_language_change(lang)


# ─── Singleton Instance ───────────────────────
interaction_loop = InteractionLoop()