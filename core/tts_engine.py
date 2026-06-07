# ─────────────────────────────────────────────
# TTS ENGINE — Text to Speech
# English: en-US-AriaNeural (Edge TTS)
# Arabic:  ar-OM-AbdullahNeural (Edge TTS)
# ─────────────────────────────────────────────

import asyncio
import os
import tempfile
import threading
import pygame
import edge_tts
from config.config_manager import config


# ─────────────────────────────────────────────
# TTS ENGINE CLASS
# ─────────────────────────────────────────────
class TTSEngine:

    # ─── Voice Map ────────────────────────────
    VOICES = {
        "en": "en-US-AriaNeural",
        "ar": "ar-OM-AbdullahNeural",
    }

    def __init__(self):
        # ─── Init pygame mixer for audio ──────
        pygame.mixer.init()
        self.is_speaking = False
        self._temp_files = []

    # ─────────────────────────────────────────
    # MAIN SPEAK METHOD
    # Call this from anywhere in the app
    # ─────────────────────────────────────────
    def speak(self, text: str, language: str = "en",
              on_start=None, on_finish=None):
        """
        Convert text to speech and play it.
        Runs in background thread to not block UI.

        Args:
            text: Text to speak
            language: 'en' or 'ar'
            on_start: callback when speech starts
            on_finish: callback when speech ends
        """
        if not text or not text.strip():
            return

        thread = threading.Thread(
            target=self._speak_thread,
            args=(text, language, on_start, on_finish),
            daemon=True
        )
        thread.start()

    # ─── Background Thread ────────────────────
    def _speak_thread(self, text, language, on_start, on_finish):
        try:
            self.is_speaking = True

            # Fire on_start callback
            if on_start:
                on_start()

            # Run async TTS in thread
            asyncio.run(self._generate_and_play(text, language))

        except Exception as e:
            print(f"[TTS ERROR] {e}")
        finally:
            self.is_speaking = False
            # Fire on_finish callback
            if on_finish:
                on_finish()

    # ─── Generate Audio + Play ────────────────
    async def _generate_and_play(self, text: str, language: str):
        """Generate audio file using Edge TTS then play it."""

        # Get correct voice
        voice = self.VOICES.get(language, self.VOICES["en"])

        # Create temp file for audio
        tmp = tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False
        )
        tmp_path = tmp.name
        tmp.close()

        # ─── Generate with Edge TTS ───────────
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(tmp_path)

        # ─── Play with pygame ─────────────────
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        # Wait until done playing
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        # Cleanup temp file
        self._cleanup_file(tmp_path)

    # ─── Stop Speaking ────────────────────────
    def stop(self):
        """Stop current speech immediately."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_speaking = False

    # ─── Cleanup Temp Files ───────────────────
    def _cleanup_file(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # ─── Test Voice ───────────────────────────
    def test_voices(self):
        """Quick test for both voices."""
        print("[TTS] Testing English voice (Aria)...")
        self.speak(
            "Hello! I am Aria, your intelligent greeting assistant.",
            language="en"
        )
        import time
        time.sleep(4)

        print("[TTS] Testing Arabic voice (Abdullah)...")
        self.speak(
            "مرحباً! أنا آريا، مساعدتك الذكية.",
            language="ar"
        )


# ─── Singleton Instance ───────────────────────
tts = TTSEngine()