import asyncio
import os
import queue
import tempfile
import threading
import time

import edge_tts
import pygame

from config.config_manager import config


class TTSEngine:

    VOICES = {
        "en": "en-US-AriaNeural",
        "ar": "ar-OM-AbdullahNeural",
    }

    def __init__(self):
        pygame.mixer.init()
        self.is_speaking = False
        self._stop_flag = False

    # ─────────────────────────────────────────
    # STANDARD SPEAK — full text at once
    # ─────────────────────────────────────────
    def speak(self, text: str, language: str = "en",
              on_start=None, on_finish=None):
        """Synthesise and play a complete text block in a background thread."""
        if not text or not text.strip():
            return

        thread = threading.Thread(
            target=self._speak_thread,
            args=(text, language, on_start, on_finish),
            daemon=True,
        )
        thread.start()

    def _speak_thread(self, text, language, on_start, on_finish):
        try:
            self.is_speaking = True
            if on_start:
                on_start()
            asyncio.run(self._generate_and_play(text, language))
        except Exception as e:
            print(f"[TTS ERROR] {e}")
        finally:
            self.is_speaking = False
            if on_finish:
                on_finish()

    async def _generate_and_play(self, text: str, language: str):
        voice = self.VOICES.get(language, self.VOICES["en"])
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(tmp_path)

        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not self._stop_flag:
            await asyncio.sleep(0.05)

        self._cleanup_file(tmp_path)

    # ─────────────────────────────────────────
    # STREAMING SPEAK — sentence by sentence
    # Synthesises sentence N+1 while playing N
    # ─────────────────────────────────────────
    def speak_streamed(self, sentence_generator, language: str = "en",
                       on_play_start=None):
        """
        Accept a generator of sentences and play them as they arrive.
        Returns immediately; sets is_speaking=True until all audio is done.

        on_play_start: called once when the first audio clip starts playing.
        """
        self._stop_flag = False
        self.is_speaking = True

        thread = threading.Thread(
            target=self._stream_worker,
            args=(sentence_generator, language, on_play_start),
            daemon=True,
        )
        thread.start()

    def _stream_worker(self, sentence_generator, language, on_play_start):
        """
        Two-stage pipeline inside a single background thread:
          Stage 1 (sub-thread): sentence → Edge TTS → temp file → synth_q
          Stage 2 (this thread): temp file → pygame playback
        """
        synth_q = queue.Queue()
        voice = self.VOICES.get(language, self.VOICES["en"])

        # ── Stage 1: synthesiser sub-thread ──
        def synthesiser():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for sentence in sentence_generator:
                    if self._stop_flag:
                        break
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    try:
                        tmp = tempfile.NamedTemporaryFile(
                            suffix=".mp3", delete=False
                        )
                        tmp_path = tmp.name
                        tmp.close()
                        loop.run_until_complete(
                            self._synthesise_to_file(sentence, voice, tmp_path)
                        )
                        synth_q.put(tmp_path)
                    except Exception as e:
                        print(f"[TTS SYNTH] {e}")
            finally:
                loop.close()
                synth_q.put(None)  # sentinel: no more files

        synth_thread = threading.Thread(target=synthesiser, daemon=True)
        synth_thread.start()

        # ── Stage 2: player ──
        first_played = False
        try:
            while True:
                try:
                    path = synth_q.get(timeout=15)
                except queue.Empty:
                    print("[TTS] Timeout waiting for synthesised audio.")
                    break

                if path is None:
                    break

                if self._stop_flag:
                    self._cleanup_file(path)
                    continue

                if not first_played:
                    if on_play_start:
                        on_play_start()
                    first_played = True

                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and not self._stop_flag:
                        time.sleep(0.05)
                except Exception as e:
                    print(f"[TTS PLAY] {e}")
                finally:
                    self._cleanup_file(path)
        finally:
            self.is_speaking = False

    async def _synthesise_to_file(self, text: str, voice: str, path: str):
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(path)

    # ─────────────────────────────────────────
    # STOP
    # ─────────────────────────────────────────
    def stop(self):
        self._stop_flag = True
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_speaking = False

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def _cleanup_file(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def test_voices(self):
        print("[TTS] Testing English voice...")
        self.speak(
            "Hello! I am your intelligent greeting assistant.",
            language="en",
        )
        time.sleep(4)
        print("[TTS] Testing Arabic voice...")
        self.speak("مرحباً! أنا مساعدتك الذكية.", language="ar")


tts = TTSEngine()
