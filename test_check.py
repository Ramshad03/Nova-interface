import os

files_to_check = [
    "core/stt_engine.py",
    "core/wake_word.py",
    "core/interaction_loop.py",
    "core/tts_engine.py",
    "core/ai_brain.py"
]

keywords = [
    "noise_threshold",
    "noise_baseline",
    "calibrat",
    "no_speech_threshold",
]

print("=== Threshold Check ===\n")

for filepath in files_to_check:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        found = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for kw in keywords:
                if kw.lower() in line.lower():
                    found.append(f"  Line {i}: {line.rstrip()}")
                    break

        if found:
            print(f"⚠️  {filepath}:")
            for item in found:
                print(item)
        else:
            print(f"✅ {filepath} — CLEAN")
    else:
        print(f"❌ {filepath} — FILE NOT FOUND")

print("\n=== Done ===")