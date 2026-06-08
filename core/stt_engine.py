from collections import deque
from contextlib import redirect_stderr, redirect_stdout
import io
import time
import threading

import numpy as np
import soundfile as sf
import whisper

from config.config_manager import config
from core.audio_stream import audio_stream


class STTEngine:
    LANGUAGE_MAP = {
        "en": "en",
        "ar": "ar",
        "english": "en",
        "arabic": "ar",
    }

    def __init__(self):
        self.model = None
        self.groq_client = None
        self.is_recording = False
        self.sample_rate = audio_stream.sample_rate
        self.model_name = config.get("audio", "whisper_model", default="base")

        self._barge_in_stop = threading.Event()
        self._barge_in_detected = threading.Event()
        self._barge_in_buffer: list = []
        self._barge_in_thread: threading.Thread | None = None
        self._barge_in_on_detected = None   # callback fired the instant voice is confirmed

        audio_stream.start()
        self._setup_remote_client()
        print(f"[STT] Loading local Whisper fallback model: {self.model_name}")
        self._load_model()
        print("[STT] Speech engine ready")

    def _setup_remote_client(self):
        try:
            if config.groq_api_key:
                from groq import Groq
                self.groq_client = Groq(api_key=config.groq_api_key)
                print("[STT] Groq speech-to-text enabled")
        except Exception as error:
            self.groq_client = None
            print(f"[STT] Groq STT unavailable: {error}")

    def _load_model(self):
        try:
            self.model = whisper.load_model(self.model_name)
        except Exception as error:
            print(f"[STT ERROR] Failed to load local model: {error}")
            raise

    # ─────────────────────────────────────────
    # RECORDING — reads from the always-on stream
    # ─────────────────────────────────────────

    def drain(self) -> None:
        """Discard buffered mic audio — call after TTS to prevent echo capture."""
        audio_stream.drain()

    def reload_model(self) -> None:
        """Reload the local Whisper model — called when the user changes the model in UI Settings."""
        new_name = config.get("audio", "whisper_model", default="base")
        if new_name == self.model_name:
            return
        print(f"[STT] Reloading Whisper model: {self.model_name} → {new_name}")
        self.model_name = new_name

        def _bg():
            try:
                import whisper as _whisper
                self.model = _whisper.load_model(self.model_name)
                print(f"[STT] Whisper model '{self.model_name}' ready")
            except Exception as e:
                print(f"[STT ERROR] Model reload failed: {e}")

        threading.Thread(target=_bg, daemon=True).start()

    def record_audio(self, on_speech_start=None, on_partial_audio=None) -> np.ndarray:
        """
        Records until the user genuinely stops speaking.

        Silence requirement is adaptive: the longer the utterance so far,
        the more sustained silence is needed before we conclude the person
        is done.  This prevents mid-sentence pauses from cutting off a long
        question while still being responsive after a short one.

            required_silence = 1.0 s  +  0.08 × spoken_seconds  (max 3.5 s)

        Practical examples
        ------------------
        •  3 s question  →  needs  ~1.2 s of silence to end
        • 10 s question  →  needs  ~1.8 s of silence to end
        • 20 s question  →  needs  ~2.6 s of silence to end
        • 35 s+ question →  needs   3.5 s of silence to end (cap)

        Also exits if nobody speaks within 8 s, or stop() is called.
        on_speech_start: zero-argument callback fired at first voice detection.
        """
        audio_stream.drain()
        self.is_recording = True
        print("[STT] Listening...")

        chunk_dur           = audio_stream.chunk_samples / self.sample_rate  # 0.1 s
        max_wait_for_speech = 8.0
        pre_roll_chunks     = 3
        speech_confirm_chunks = 2

        recorded             = 0.0
        speech_started       = False
        speech_started_at    = 0.0
        silent_count         = 0
        chunks: list         = []
        lead_in              = deque(maxlen=pre_roll_chunks)
        noise_floor          = None
        peak_rms             = 0.0
        last_partial_at      = 0.0   # spoken_for value when last partial was fired
        partial_interval_s   = 2.5   # fire a partial transcription every N seconds of speech
        voiced_count         = 0

        while self.is_recording:
            chunk = audio_stream.read(timeout=0.3)
            if chunk is None:
                continue

            recorded += chunk_dur
            rms = float(np.sqrt(np.mean(np.square(chunk))) + 1e-9)
            peak_rms = max(peak_rms, rms)

            if noise_floor is None:
                noise_floor = rms
            else:
                noise_floor = noise_floor * 0.96 + rms * 0.04

            silence_threshold = max(noise_floor * 1.8, 0.004)
            is_silent = rms < silence_threshold

            if not speech_started:
                lead_in.append(chunk)
                if not is_silent:
                    voiced_count += 1
                    if voiced_count >= speech_confirm_chunks:
                        speech_started = True
                        speech_started_at = recorded
                        chunks.extend(list(lead_in))
                        silent_count = 0
                        if on_speech_start:
                            on_speech_start()
                else:
                    voiced_count = 0
                if recorded >= max_wait_for_speech and not speech_started:
                    break
                continue

            chunks.append(chunk)

            if is_silent:
                silent_count += 1
            else:
                silent_count = 0

            spoken_for = recorded - speech_started_at

            # Fire partial audio callback every 2.5 s so the caller can show
            # live partial transcription while recording continues.
            if on_partial_audio and spoken_for - last_partial_at >= partial_interval_s:
                on_partial_audio(np.concatenate(chunks).astype(np.float32, copy=False))
                last_partial_at = spoken_for

            # Adaptive silence gate — base of 2.0 s matches standard voice
            # assistant behaviour and prevents mid-sentence cutoffs on natural
            # breathing / thinking pauses.  Grows slowly for longer utterances.
            required_silence_s = 2.0 + min(spoken_for * 0.04, 2.0)
            required_chunks = int(required_silence_s / chunk_dur)

            if spoken_for >= 0.5 and silent_count >= required_chunks:
                break

        self.is_recording = False

        if not chunks:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(chunks).astype(np.float32, copy=False)
        print(f"[STT] Captured {len(audio) / self.sample_rate:.2f}s audio, peak rms={peak_rms:.4f}")
        return audio

    # ─────────────────────────────────────────
    # TRANSCRIPTION
    # ─────────────────────────────────────────

    def transcribe(self, audio: np.ndarray, language_hint: str | None = None) -> dict:
        if audio is None or len(audio) == 0:
            return {"text": "", "language": "en"}

        audio = self._trim_silence(audio)
        if len(audio) < int(self.sample_rate * 0.45):
            return {"text": "", "language": "en"}

        remote_result = self._transcribe_with_groq(audio, language_hint)
        if remote_result.get("text"):
            return remote_result

        return self._transcribe_with_local_whisper(audio, language_hint)

    def _transcribe_with_groq(self, audio: np.ndarray, language_hint: str | None) -> dict:
        if not self.groq_client:
            return {"text": "", "language": "en"}

        try:
            wav_bytes = self._audio_to_wav_bytes(audio)
            model = (
                "whisper-large-v3-turbo"
                if (language_hint or "en") == "en"
                else "whisper-large-v3"
            )
            request = {
                "file": ("speech.wav", wav_bytes),
                "model": model,
                "temperature": 0.0,
                "response_format": "json",
            }
            if language_hint:
                request["language"] = self.LANGUAGE_MAP.get(
                    language_hint.lower(), language_hint.lower()
                )

            response = self.groq_client.audio.transcriptions.create(**request)
            text = (getattr(response, "text", "") or "").strip()
            lang = self.LANGUAGE_MAP.get(
                (language_hint or "en").lower(), language_hint or "en"
            )

            if text:
                text = self._apply_vocabulary_corrections(text, lang)
                if not self._is_hallucination(text, lang):
                    print(f"[STT] '{text}' ({lang}) via Groq")
                    return {"text": text, "language": lang, "raw_language": lang}
        except Exception as error:
            print(f"[STT] Groq transcription failed, using local fallback: {error}")

        return {"text": "", "language": "en"}

    def _transcribe_with_local_whisper(self, audio: np.ndarray, language_hint: str | None) -> dict:
        if self.model is None:
            return {"text": "", "language": "en"}

        audio = np.asarray(audio, dtype=np.float32)
        peak = float(np.max(np.abs(audio)) + 1e-9)
        audio = audio / peak

        attempts = []
        if language_hint:
            attempts.append(self.LANGUAGE_MAP.get(language_hint.lower(), "en"))
        else:
            attempts.extend([None, "en", "ar"])

        for attempt_lang in attempts:
            try:
                whisper_kwargs = {
                    "task": "transcribe",
                    "fp16": False,
                    "verbose": None,
                    "condition_on_previous_text": False,
                    "temperature": 0.0,
                    "compression_ratio_threshold": 2.4,
                    "logprob_threshold": -1.0,
                    "no_speech_threshold": 0.6,
                    "language": attempt_lang,
                }

                muted_stdout = io.StringIO()
                muted_stderr = io.StringIO()
                with redirect_stdout(muted_stdout), redirect_stderr(muted_stderr):
                    result = self.model.transcribe(audio, **whisper_kwargs)

                text = result.get("text", "").strip()
                detected_lang = result.get("language", attempt_lang or "en")
                lang = self.LANGUAGE_MAP.get(detected_lang.lower(), "en")
                text = self._apply_vocabulary_corrections(text, lang)

                if text and not self._is_hallucination(text, lang):
                    print(f"[STT] '{text}' ({lang}) via local Whisper")
                    return {"text": text, "language": lang, "raw_language": detected_lang}
            except Exception as error:
                print(f"[STT ERROR] Local Whisper attempt failed: {error}")

        return {"text": "", "language": "en"}

    # ─────────────────────────────────────────
    # BARGE-IN — interruption during TTS playback
    # ─────────────────────────────────────────

    @property
    def barge_in_detected(self) -> bool:
        return self._barge_in_detected.is_set()

    def start_barge_in_monitor(self, on_barge_in=None) -> None:
        """
        on_barge_in: zero-argument callable fired immediately in the worker
        thread the moment voice is confirmed.  Use it to stop TTS and switch
        UI state without waiting for the 50 ms polling interval.
        """
        self._barge_in_on_detected = on_barge_in
        self._barge_in_stop.clear()
        self._barge_in_detected.clear()
        self._barge_in_buffer = []
        self._barge_in_thread = threading.Thread(
            target=self._barge_in_worker, daemon=True
        )
        self._barge_in_thread.start()

    def stop_barge_in_monitor(self) -> None:
        self._barge_in_stop.set()
        if self._barge_in_thread and self._barge_in_thread.is_alive():
            # Worker checks stop every 0.05 s, so 1 s is more than enough.
            self._barge_in_thread.join(timeout=1.0)
        self._barge_in_buffer = []
        self._barge_in_detected.clear()

    def _barge_in_worker(self) -> None:
        """
        Three-phase pipeline:

        Phase 0 – onset delay (150 ms)
            Let TTS start producing audio before we touch the mic stream.

        Phase 1 – echo calibration (500 ms)
            Sample the mic WHILE TTS IS ACTIVELY PLAYING to measure the actual
            speaker-bleed level in this specific room / speaker / mic setup.
            Threshold is set to 2.2 × the 85th-percentile of that measured
            echo, with a hard floor of 0.018.  This means the system adapts
            automatically — loud speakers raise the threshold; quiet ones
            lower it — so the response can never trigger itself.

        Phase 2 – detection / capture loop
            Monitor for the user's voice above the calibrated threshold.
            Three consecutive chunks (300 ms) confirm deliberate speech.
        """
        chunk_dur = audio_stream.chunk_samples / self.sample_rate  # 0.1 s

        # ── Phase 0: onset delay ──────────────────────────────────────
        time.sleep(0.15)
        audio_stream.drain()

        # ── Phase 1: calibrate echo level ────────────────────────────
        echo_rms: list = []
        calibrate_until = time.time() + 0.5
        while time.time() < calibrate_until and not self._barge_in_stop.is_set():
            chunk = audio_stream.read(timeout=0.05)
            if chunk is not None:
                echo_rms.append(float(np.sqrt(np.mean(np.square(chunk))) + 1e-9))

        if self._barge_in_stop.is_set():
            return

        if echo_rms:
            echo_rms.sort()
            p85 = echo_rms[int(len(echo_rms) * 0.85)]    # 85th-percentile echo
            barge_threshold = max(p85 * 2.2, 0.018)       # well above echo, hard floor
        else:
            barge_threshold = 0.018

        print(f"[STT] Barge-in threshold calibrated to {barge_threshold:.4f}")
        audio_stream.drain()   # discard calibration audio before we start detecting

        # ── Phase 2: detection / capture ─────────────────────────────
        consecutive = 0
        pre_roll: deque = deque(maxlen=6)   # 600 ms look-back
        phase       = "detecting"
        capture: list = []
        captured_dur  = 0.0
        silent_count  = 0

        while not self._barge_in_stop.is_set():
            chunk = audio_stream.read(timeout=0.05)
            if chunk is None:
                continue

            if self._barge_in_stop.is_set():
                break

            rms = float(np.sqrt(np.mean(np.square(chunk))) + 1e-9)

            if phase == "detecting":
                pre_roll.append(chunk)
                if rms > barge_threshold:
                    consecutive += 1
                    if consecutive >= 3:   # 300 ms sustained voice confirms intent
                        capture = list(pre_roll)
                        captured_dur = len(capture) * chunk_dur
                        self._barge_in_detected.set()
                        if self._barge_in_on_detected:
                            try:
                                self._barge_in_on_detected()
                            except Exception:
                                pass
                        phase = "capturing"
                        silent_count = 0
                else:
                    consecutive = 0

            elif phase == "capturing":
                capture.append(chunk)
                captured_dur += chunk_dur
                required_silence_s = 1.0 + min(captured_dur * 0.08, 2.5)
                required_chunks = int(required_silence_s / chunk_dur)
                if rms < max(barge_threshold * 0.5, 0.005):
                    silent_count += 1
                else:
                    silent_count = 0
                if (silent_count >= required_chunks and captured_dur >= 0.5) or captured_dur >= 30.0:
                    self._barge_in_buffer = capture
                    return

        if phase == "capturing" and capture:
            self._barge_in_buffer = capture

    def get_barge_in_result(self, language_hint: str | None = None) -> dict:
        """Block until the barge-in worker finishes capturing, then transcribe."""
        if self._barge_in_thread and self._barge_in_thread.is_alive():
            self._barge_in_thread.join(timeout=12)
        if not self._barge_in_buffer:
            return {"text": "", "language": "en"}
        audio = np.concatenate(self._barge_in_buffer).astype(np.float32)
        print(f"[STT] Barge-in captured {len(audio) / self.sample_rate:.2f}s audio")
        return self.transcribe(audio, language_hint=language_hint)

    # ─────────────────────────────────────────
    # PUBLIC HELPERS
    # ─────────────────────────────────────────

    def listen(
        self,
        language_hint: str | None = None,
        on_speech_start=None,
        on_partial_text=None,
    ) -> dict:
        """
        on_partial_text(text: str): fired every ~2.5 s of captured speech with
        a Groq transcription of the audio accumulated so far.  Use it to update
        the UI in real-time while the user is still talking.
        """
        _partial_id = [0]   # version counter — only the latest result is shown

        def _on_partial_audio(audio_so_far: np.ndarray):
            if not on_partial_text:
                return
            _partial_id[0] += 1
            my_id = _partial_id[0]
            snapshot = audio_so_far.copy()

            def _bg():
                result = self._transcribe_with_groq(snapshot, language_hint)
                text = result.get("text", "").strip()
                # Discard if a newer partial has already started
                if text and my_id == _partial_id[0]:
                    on_partial_text(text)

            threading.Thread(target=_bg, daemon=True).start()

        audio = self.record_audio(
            on_speech_start=on_speech_start,
            on_partial_audio=_on_partial_audio if on_partial_text else None,
        )
        if len(audio) == 0:
            return {"text": "", "language": "en"}
        return self.transcribe(audio, language_hint=language_hint)

    def stop(self):
        self.is_recording = False
        audio_stream.drain()   # discard buffered chunks; stream stays running

    # ─────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────

    def _apply_vocabulary_corrections(self, text: str, language: str) -> str:
        try:
            from core.vocabulary.corrector import corrector
            return corrector.correct(text, language=language)
        except Exception:
            return text

    def _audio_to_wav_bytes(self, audio: np.ndarray) -> bytes:
        buffer = io.BytesIO()
        sf.write(buffer, audio, self.sample_rate, format="WAV")
        return buffer.getvalue()

    def _trim_silence(self, audio: np.ndarray) -> np.ndarray:
        if audio is None or len(audio) == 0:
            return np.array([], dtype=np.float32)

        energy = np.abs(audio)
        threshold = max(float(np.max(energy)) * 0.05, 0.002)
        active = np.where(energy > threshold)[0]

        if len(active) == 0:
            return np.array([], dtype=np.float32)

        pad = int(self.sample_rate * 0.16)
        start = max(0, int(active[0]) - pad)
        end = min(len(audio), int(active[-1]) + pad)
        return audio[start:end]

    def _is_hallucination(self, text: str, lang: str) -> bool:
        if not text or len(text.strip()) < 2:
            return True

        text_lower = text.lower().strip()
        garbage = [
            "thank you for watching",
            "thanks for watching",
            "please subscribe",
            "subtitles by",
            "transcribed by",
            "bye",
            "bye.",
            "you",
            "you.",
        ]
        if text_lower in garbage:
            return True

        if lang == "en":
            non_latin = sum(1 for c in text if ord(c) > 591)
            if len(text) > 2 and non_latin / len(text) > 0.25:
                print(f"[STT] Rejected foreign-script hallucination: '{text}'")
                return True

        return False


stt = STTEngine()
