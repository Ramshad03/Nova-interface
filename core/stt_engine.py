# ─────────────────────────────────────────────
# STT ENGINE — Speech to Text
# Uses OpenAI Whisper (local)
# No threshold filtering — maximum sensitivity
# Whisper handles all noise filtering naturally
# ─────────────────────────────────────────────

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
import soundfile as sf
import threading


# ─────────────────────────────────────────────
# STT ENGINE CLASS
# ─────────────────────────────────────────────
class STTEngine:

    LANGUAGE_MAP = {
        "en":      "en",
        "ar":      "ar",
        "english": "en",
        "arabic":  "ar",
    }

    def __init__(self):
        self.model       = None
        self.is_recording = False
        self.sample_rate  = 16000
        self.channels     = 1

        print("[STT] Loading Whisper model...")
        self._load_model()
        print("[STT] Whisper model ready ✅")

    # ─── Load Model ───────────────────────────
    def _load_model(self):
        try:
            self.model = whisper.load_model("base")
        except Exception as e:
            print(f"[STT ERROR] Failed to load model: {e}")
            raise

    # ─────────────────────────────────────────
    # RECORD AUDIO
    # Records until silence detected
    # No threshold — fully sensitive
    # ─────────────────────────────────────────
    def record_audio(self, duration: int = 6) -> np.ndarray:
        """
        Record audio until user stops speaking.
        Maximum sensitivity — no filtering.
        """
        self.is_recording = True
        print("[STT] Listening...")

        chunks       = []
        silent_count = 0
        max_silence  = 8    # 8 × 0.3s = 2.4s silence to stop
        max_duration = duration
        recorded     = 0.0
        chunk_dur    = 0.3
        started      = False

        while recorded < max_duration:
            if not self.is_recording:
                break

            chunk = sd.rec(
                int(chunk_dur * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32"
            )
            sd.wait()
            chunk = chunk.flatten()
            chunks.append(chunk)
            recorded += chunk_dur

            # ─── Detect any audio activity ────
            # No threshold — stop on natural silence
            rms = np.sqrt(np.mean(chunk ** 2))
            is_silent = rms < 0.001

            if not is_silent:
                silent_count = 0
                started = True
            else:
                silent_count += 1

            # ─── Stop after silence ───────────
            if started and silent_count >= max_silence:
                print(f"[STT] Done at {recorded:.1f}s")
                break

        self.is_recording = False
        return np.concatenate(chunks) if chunks else np.array([])

    # ─────────────────────────────────────────
    # TRANSCRIBE
    # ─────────────────────────────────────────
    def transcribe(self, audio: np.ndarray) -> dict:
        """Transcribe audio using Whisper."""

        if self.model is None:
            return {"text": "", "language": "en"}

        if audio is None or len(audio) == 0:
            return {"text": "", "language": "en"}

        # ─── Minimum length check ─────────────
        if len(audio) < self.sample_rate * 0.5:
            return {"text": "", "language": "en"}

        try:
            # ─── Pad to 30 seconds ────────────
            target = self.sample_rate * 30
            if len(audio) < target:
                audio = np.pad(
                    audio,
                    (0, target - len(audio)),
                    mode="constant"
                )

            # ─── Save temp WAV ────────────────
            tmp = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            )
            tmp_path = tmp.name
            tmp.close()
            sf.write(tmp_path, audio, self.sample_rate)

            # ─── Transcribe ───────────────────
            result = self.model.transcribe(
                tmp_path,
                language=None,
                task="transcribe",
                fp16=False,
                verbose=False,
                condition_on_previous_text=False,
            )

            text          = result.get("text", "").strip()
            detected_lang = result.get("language", "en")
            lang          = self.LANGUAGE_MAP.get(
                detected_lang.lower(), "en"
            )

            # ─── Apply vocabulary corrections ─
            try:
                from core.vocabulary.corrector import corrector
                text = corrector.correct(text, language=lang)
            except Exception:
                pass

            # ─── Filter obvious hallucinations ─
            if self._is_hallucination(text, detected_lang):
                self._cleanup(tmp_path)
                return {"text": "", "language": "en"}

            if text:
                print(f"[STT] '{text}' ({lang})")

            self._cleanup(tmp_path)
            return {
                "text":         text,
                "language":     lang,
                "raw_language": detected_lang
            }

        except Exception as e:
            print(f"[STT ERROR] {e}")
            return {"text": "", "language": "en"}

    # ─────────────────────────────────────────
    # HALLUCINATION FILTER
    # Only filters obvious non-speech
    # ─────────────────────────────────────────
    def _is_hallucination(self, text: str, lang: str) -> bool:
        """Filter only obvious Whisper hallucinations."""
        if not text or len(text.strip()) < 2:
            return True

        # ─── Known garbage phrases ────────────
        garbage = [
            "thank you for watching",
            "thanks for watching",
            "please subscribe",
            "subtitles by",
            "transcribed by",
        ]
        text_lower = text.lower().strip()
        for phrase in garbage:
            if text_lower == phrase:
                return True

        return False

    # ─────────────────────────────────────────
    # LISTEN — Record + Transcribe
    # ─────────────────────────────────────────
    def listen(self, duration: int = 6) -> dict:
        """Record and transcribe in one call."""
        audio = self.record_audio(duration)
        if len(audio) == 0:
            return {"text": "", "language": "en"}
        return self.transcribe(audio)

    # ─── Stop ─────────────────────────────────
    def stop(self):
        self.is_recording = False
        sd.stop()

    # ─── Cleanup ──────────────────────────────
    def _cleanup(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


# ─── Singleton Instance ───────────────────────
stt = STTEngine()