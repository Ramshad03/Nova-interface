# ─────────────────────────────────────────────
# VOCABULARY TRAINER — Developer Tool
# Add, remove, list, test vocabulary corrections
# Run: python core/vocabulary/vocabulary_trainer.py
# ─────────────────────────────────────────────

import json
import os
import sys
from pathlib import Path
from datetime import date

# ─── Paths ────────────────────────────────────
VOCAB_DIR = Path(__file__).parent
EN_FILE   = VOCAB_DIR / "en_vocabulary.json"
AR_FILE   = VOCAB_DIR / "ar_vocabulary.json"


# ─────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────
def load_vocab(lang: str) -> dict:
    path = EN_FILE if lang == "en" else AR_FILE
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vocab(data: dict, lang: str):
    path = EN_FILE if lang == "en" else AR_FILE
    # Update last_updated
    data["_metadata"]["last_updated"] = str(date.today())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved to {path.name}")


# ─────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────
def cmd_list(lang: str):
    """List all corrections."""
    data = load_vocab(lang)
    corrections = data.get("corrections", {})
    lang_name = "English" if lang == "en" else "Arabic"

    print(f"\n{'='*55}")
    print(f"  {lang_name} Vocabulary — {len(corrections)} corrections")
    print(f"  Version: {data['_metadata']['version']}")
    print(f"{'='*55}")

    for i, (wrong, correct) in enumerate(corrections.items(), 1):
        print(f"  {i:3}. '{wrong}' → '{correct}'")

    print(f"{'='*55}\n")


def cmd_add(lang: str, wrong: str, correct: str):
    """Add a new correction."""
    data = load_vocab(lang)

    if wrong in data["corrections"]:
        print(f"⚠️  '{wrong}' already exists → '{data['corrections'][wrong]}'")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Cancelled.")
            return

    data["corrections"][wrong] = correct
    save_vocab(data, lang)
    print(f"✅ Added: '{wrong}' → '{correct}'")


def cmd_remove(lang: str, wrong: str):
    """Remove a correction."""
    data = load_vocab(lang)

    if wrong not in data["corrections"]:
        print(f"❌ '{wrong}' not found in vocabulary")
        return

    del data["corrections"][wrong]
    save_vocab(data, lang)
    print(f"✅ Removed: '{wrong}'")


def cmd_test(lang: str, text: str):
    """Test correction on a phrase."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.vocabulary.corrector import corrector

    corrector.reload()
    result = corrector.correct(text, language=lang)

    print(f"\nInput:  '{text}'")
    print(f"Output: '{result}'")
    if result != text:
        print("✅ Correction applied!")
    else:
        print("ℹ️  No correction needed")


def cmd_version_bump(lang: str):
    """Bump version number."""
    data = load_vocab(lang)
    current = data["_metadata"]["version"]
    parts = current.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    new_version = ".".join(parts)
    data["_metadata"]["version"] = new_version
    save_vocab(data, lang)
    print(f"✅ Version bumped: {current} → {new_version}")


def cmd_stats():
    """Show stats for both vocabularies."""
    for lang in ["en", "ar"]:
        data = load_vocab(lang)
        meta = data["_metadata"]
        corrections = data.get("corrections", {})
        lang_name = "English" if lang == "en" else "Arabic"
        print(f"\n{lang_name}:")
        print(f"  Version:      {meta['version']}")
        print(f"  Last updated: {meta['last_updated']}")
        print(f"  Corrections:  {len(corrections)}")


# ─────────────────────────────────────────────
# INTERACTIVE MENU
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  ALEXA ROBOT — Vocabulary Trainer")
    print("  Developer Tool v1.0.0")
    print("="*55)

    while True:
        print("\nCommands:")
        print("  1. List corrections (English)")
        print("  2. List corrections (Arabic)")
        print("  3. Add correction (English)")
        print("  4. Add correction (Arabic)")
        print("  5. Remove correction (English)")
        print("  6. Remove correction (Arabic)")
        print("  7. Test correction (English)")
        print("  8. Test correction (Arabic)")
        print("  9. Bump version (English)")
        print("  10. Bump version (Arabic)")
        print("  11. Show stats")
        print("  0. Exit")
        print()

        choice = input("Enter choice: ").strip()

        if choice == "0":
            print("Exiting trainer.")
            break

        elif choice == "1":
            cmd_list("en")

        elif choice == "2":
            cmd_list("ar")

        elif choice == "3":
            wrong   = input("Wrong phrase (what Whisper hears): ").strip()
            correct = input("Correct phrase (what it should be): ").strip()
            if wrong and correct:
                cmd_add("en", wrong, correct)

        elif choice == "4":
            wrong   = input("Wrong phrase (what Whisper hears): ").strip()
            correct = input("Correct phrase (what it should be): ").strip()
            if wrong and correct:
                cmd_add("ar", wrong, correct)

        elif choice == "5":
            wrong = input("Wrong phrase to remove: ").strip()
            cmd_remove("en", wrong)

        elif choice == "6":
            wrong = input("Wrong phrase to remove: ").strip()
            cmd_remove("ar", wrong)

        elif choice == "7":
            text = input("Enter English text to test: ").strip()
            cmd_test("en", text)

        elif choice == "8":
            text = input("Enter Arabic text to test: ").strip()
            cmd_test("ar", text)

        elif choice == "9":
            cmd_version_bump("en")

        elif choice == "10":
            cmd_version_bump("ar")

        elif choice == "11":
            cmd_stats()

        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()