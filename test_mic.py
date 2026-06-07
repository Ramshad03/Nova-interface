import sounddevice as sd
import numpy as np
import time

print("=== MIC DIAGNOSTIC TEST ===\n")
print("Phase 1: Stay SILENT for 3 seconds...")
time.sleep(2)

sample_rate = 16000
readings = []

for i in range(10):
    audio = sd.rec(int(0.3 * sample_rate), samplerate=sample_rate,
                   channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    readings.append(rms)
    print(f"Silent [{i+1}]: RMS={rms:.5f} | Peak={peak:.5f}")

avg_noise = np.mean(readings)
print(f"\nAverage noise RMS: {avg_noise:.5f}")
print(f"Suggested threshold: {avg_noise * 2.5:.5f}")

print("\n\nPhase 2: Speak NORMALLY for 5 seconds...")
print("Say something like 'Hello, what is photosynthesis?'")
time.sleep(1)

for i in range(10):
    audio = sd.rec(int(0.3 * sample_rate), samplerate=sample_rate,
                   channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    print(f"Speaking [{i+1}]: RMS={rms:.5f} | Peak={peak:.5f}")

print("\nDone! Paste this output so I can set the perfect threshold.")