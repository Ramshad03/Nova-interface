import re
import threading
import time

from config.config_manager import config
from core.ai_brain import ai_brain
from core.conversation_logger import conversation_logger
from core.stt_engine import stt
from core.tts_engine import tts


class InteractionLoop:
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_CAPTURING = "capturing"
    STATE_THINKING = "thinking"
    STATE_SPEAKING = "speaking"
    TTS_ECHO_SETTLE_SECONDS = 1.0

    def __init__(self):
        self.current_state = self.STATE_IDLE
        self.current_language = "en"
        self.is_running = False
        self._loop_thread = None
        self.forced_language = None

        self.on_state_change = None
        self.on_subtitle = None
        self.on_clear_subtitle = None
        self.on_language_change = None

    def start(self):
        if self.is_running:
            print("[LOOP] Already running - skipping")
            return

        self.is_running = True
        print("[LOOP] Starting interaction loop")

        self._speak_startup_greeting()

        self._loop_thread = threading.Thread(
            target=self._always_on_loop,
            daemon=True,
        )
        self._loop_thread.start()

    def stop(self):
        self.is_running = False
        stt.stop()
        tts.stop()
        print("[LOOP] Stopped.")

    def pause(self):
        self.is_running = False
        stt.stop()
        tts.stop()
        print("[LOOP] Paused")

    def resume(self):
        if self.is_running:
            return

        self.is_running = True
        print("[LOOP] Resuming")

        self._loop_thread = threading.Thread(
            target=self._always_on_loop,
            daemon=True,
        )
        self._loop_thread.start()

    def _always_on_loop(self):
        print("[LOOP] Always-on loop running")
        pending_text: str | None = None
        pending_lang: str | None = None

        while self.is_running:
            try:
                if pending_text:
                    user_text = pending_text
                    detected_lang = pending_lang or "en"
                    pending_text = None
                    pending_lang = None
                else:
                    listen_language = self.forced_language or "en"

                    self._set_state(self.STATE_LISTENING)
                    self._clear_subtitle()

                    def _on_speech_start():
                        self._set_state(self.STATE_CAPTURING)
                        self._emit_subtitle("...", "YOU")

                    def _on_partial_text(text: str):
                        # Update the subtitle live while the user is still talking
                        self._emit_subtitle(text, "YOU")

                    result = stt.listen(
                        language_hint=listen_language,
                        on_speech_start=_on_speech_start,
                        on_partial_text=_on_partial_text,
                    )

                    if not self.is_running:
                        break

                    user_text = result.get("text", "").strip()
                    detected_lang = result.get("language", "en")

                if not user_text or len(user_text) < 2:
                    self._set_state(self.STATE_IDLE)
                    time.sleep(0.15)
                    continue

                if self.forced_language:
                    detected_lang = self.forced_language
                    print(f"[LOOP] Language forced to: {detected_lang}")

                self.current_language = detected_lang
                self._emit_language(detected_lang)

                self._set_state(self.STATE_LISTENING)
                self._emit_subtitle(user_text, "YOU")
                print(f"[LOOP] USER ({detected_lang}): {user_text}")

                time.sleep(0.15)

                response_lang = self.forced_language or detected_lang

                self._set_state(self.STATE_THINKING)
                robot_name = config.get("robot", "name", default="Alexa")

                # ── Streaming pipeline ────────────────────
                accumulated = []

                def sentence_stream():
                    buf = ""
                    for chunk in ai_brain.chat_stream(
                        user_text, language=response_lang
                    ):
                        if not self.is_running:
                            return
                        buf += chunk
                        while True:
                            m = re.search(r"(?<=[.!?؟])\s", buf)
                            if not m:
                                break
                            sentence = buf[: m.start() + 1].strip()
                            buf = buf[m.end():]
                            if sentence:
                                accumulated.append(sentence)
                                self._emit_subtitle(
                                    " ".join(accumulated),
                                    robot_name.upper(),
                                )
                                yield sentence
                    remaining = buf.strip()
                    if remaining:
                        accumulated.append(remaining)
                        self._emit_subtitle(
                            " ".join(accumulated),
                            robot_name.upper(),
                        )
                        yield remaining

                def on_first_audio():
                    self._set_state(self.STATE_SPEAKING)

                tts.speak_streamed(
                    sentence_stream(),
                    language=response_lang,
                    on_play_start=on_first_audio,
                )

                # ── Barge-in monitor ──────────────────────
                # on_barge_in fires instantly in the worker thread the moment
                # voice is confirmed — stops TTS and flips the UI without
                # waiting for the poll interval.
                def _on_barge_in():
                    tts.stop()
                    self._set_state(self.STATE_CAPTURING)
                    self._emit_subtitle("...", "YOU")
                    print("[LOOP] Barge-in — TTS stopped instantly")

                stt.start_barge_in_monitor(on_barge_in=_on_barge_in)

                while tts.is_speaking and self.is_running:
                    if stt.barge_in_detected:
                        tts.stop()   # idempotent safety-net
                        break
                    time.sleep(0.05)

                if stt.barge_in_detected:
                    # Worker already capturing — wait for it to finish, then transcribe
                    barge_result = stt.get_barge_in_result(
                        language_hint=self.forced_language or self.current_language
                    )
                    stt.stop_barge_in_monitor()
                    # Log whatever was spoken before the interruption
                    if accumulated:
                        conversation_logger.log(
                            user_text, " ".join(accumulated), language=response_lang
                        )
                    bi_text = barge_result.get("text", "").strip()
                    if bi_text and len(bi_text) >= 2:
                        pending_text = bi_text
                        pending_lang = barge_result.get("language", detected_lang)
                        ai_brain.reset_conversation()
                        continue
                else:
                    stt.stop_barge_in_monitor()
                    # Log the complete exchange
                    if accumulated:
                        conversation_logger.log(
                            user_text, " ".join(accumulated), language=response_lang
                        )

                self._set_state(self.STATE_IDLE)
                self._clear_subtitle()
                ai_brain.reset_conversation()
                self._settle_after_tts()

            except Exception as error:
                print(f"[LOOP ERROR] {error}")
                stt.stop_barge_in_monitor()
                self._set_state(self.STATE_IDLE)
                time.sleep(0.5)

        print("[LOOP] Loop exited.")

    def _speak_startup_greeting(self):
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

        self._settle_after_tts()
        self._set_state(self.STATE_IDLE)
        self._clear_subtitle()

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

    def _settle_after_tts(self):
        # Give speaker bleed a moment to decay, then flush any queued mic audio
        # so the next listen cycle starts from a clean microphone buffer.
        time.sleep(self.TTS_ECHO_SETTLE_SECONDS)
        stt.drain()


interaction_loop = InteractionLoop()
