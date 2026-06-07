# Full pipeline test - see exactly where it breaks
import sounddevice as sd
import numpy as np
import soundfile as sf
import tempfile
import whisper

print("Loading Whisper...")
model = whisper.load_model("base")
print("Whisper ready!\n")

sample_rate = 16000

# Step 1: Calibrate
print("Calibrating noise (2 seconds silence)...")
ambient = sd.rec(int(2 * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
sd.wait()
ambient_rms = np.sqrt(np.mean(ambient.flatten() ** 2))
threshold = max(0.0018, ambient_rms * 2.5)
print(f"Noise: {ambient_rms:.5f} | Threshold: {threshold:.5f}\n")

# Step 2: Detect voice
print("Speak now — testing detection (10 seconds)...")
import time
start = time.time()
detected = False

while time.time() - start < 10:
    chunk = sd.rec(int(0.3 * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    chunk = chunk.flatten()
    rms = np.sqrt(np.mean(chunk ** 2))
    peak = np.max(np.abs(chunk))
    print(f"RMS={rms:.5f} Peak={peak:.5f} | {'✅ VOICE!' if rms > threshold else '❌ noise'}")
    
    if rms > threshold:
        detected = True
        print("\n✅ Voice detected! Now recording 5 seconds...")
        
        audio = sd.rec(int(5 * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        audio = audio.flatten()
        
        # Save and transcribe
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, sample_rate)
        
        print("Transcribing...")
        result = model.transcribe(tmp.name, fp16=False, verbose=False)
        print(f"\n🎤 You said: '{result['text']}'")
        print(f"🌐 Language: {result['language']}")
        break

if not detected:
    print("\n❌ No voice detected in 10 seconds")
    print(f"Your voice RMS needs to be above: {threshold:.5f}")