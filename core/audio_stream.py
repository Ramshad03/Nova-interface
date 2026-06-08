import queue

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
CHUNK_DURATION = 0.1        # 100 ms per chunk
CHUNK_SAMPLES = int(CHUNK_DURATION * SAMPLE_RATE)


class AudioStream:
    """
    Always-on, low-latency microphone input using sd.InputStream.

    A single stream feeds both the STT recording pipeline and the barge-in
    monitor.  This eliminates the gaps and concurrency hazards of repeated
    sd.rec() calls: audio is captured continuously in the PortAudio callback
    thread and queued for whatever consumer is currently active.

    Usage
    -----
    • Call start() once at application startup.
    • Call drain() before each fresh recording to discard stale chunks.
    • Call read() in a loop to consume chunks (blocks up to `timeout` sec).
    • Only one consumer should read at a time (no concurrent readers).
    """

    def __init__(self) -> None:
        self.sample_rate = SAMPLE_RATE
        self.chunk_samples = CHUNK_SAMPLES
        self._q: queue.Queue = queue.Queue(maxsize=300)   # ~30 s back-pressure cap
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        if self._stream is not None:
            return
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_samples,
            callback=self._callback,
        )
        self._stream.start()
        print("[AUDIO] Continuous mic stream started")

    def _callback(
        self, indata: np.ndarray, frames: int, time_info, status
    ) -> None:
        # Runs in the PortAudio thread — keep it minimal.
        try:
            self._q.put_nowait(indata[:, 0].copy())
        except queue.Full:
            pass    # drop oldest pressure; keeps latency low

    def read(self, timeout: float = 0.3) -> np.ndarray | None:
        """Return the next 100 ms chunk, or None on timeout."""
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain(self) -> None:
        """Discard all buffered chunks — call before a fresh recording."""
        while not self._q.empty():
            try:
                self._q.get_nowait()
            except queue.Empty:
                break

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.drain()


audio_stream = AudioStream()
