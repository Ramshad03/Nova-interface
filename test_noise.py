import sounddevice as sd
import numpy as np
import time

print("Measuring your background noise level for 10 seconds...")
print("Stay quiet and don't speak...\n")

sample_rate = 16000

for i in range(10):
    audio = sd.rec(int(1 * sample_rate), samplerate=sample_rate,
                   channels=1, dtype="float32")
    sd.wait()
    rms = np.sqrt(np.mean(audio.flatten() ** 2))
    print(f"Second {i+1}: RMS = {rms:.4f}")

print("\nNow speak normally for 5 seconds...")
time.sleep(1)
for i in range(5):
    audio = sd.rec(int(1 * sample_rate), samplerate=sample_rate,
                   channels=1, dtype="float32")
    sd.wait()
    rms = np.sqrt(np.mean(audio.flatten() ** 2))
    print(f"Speaking second {i+1}: RMS = {rms:.4f}")