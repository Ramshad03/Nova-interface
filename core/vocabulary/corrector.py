# ─────────────────────────────────────────────
# VOCABULARY CORRECTOR
# Fixes STT misrecognitions using trained data
# Supports English and Arabic corrections
# Auto-loads both vocabulary files
# ─────────────────────────────────────────────

import json
import re
import os
from pathlib import Path


# ─────────────────────────────────────────────
# CORRECTOR CLASS
# ─────────────────────────────────────────────
class VocabularyCorrector:

    def __init__(self):
        self.en_corrections = {}
        self.ar_corrections = {}
        self.en_metadata = {}
        self.ar_metadata = {}
        self._load_vocabularies()

    # ─────────────────────────────────────────
    # LOAD VOCABULARY FILES
    # ─────────────────────────────────────────
    def _load_vocabularies(self):
        """Load both EN and AR vocabulary files."""
        vocab_dir = Path(__file__).parent

        # ─── English ──────────────────────────
        en_path = vocab_dir / "en_vocabulary.json"
        if en_path.exists():
            with open(en_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.en_corrections = data.get("corrections", {})
                self.en_metadata    = data.get("_metadata", {})
            print(
                f"[VOCAB] English loaded ✅ "
                f"({len(self.en_corrections)} corrections) "
                f"v{self.en_metadata.get('version', '?')}"
            )
        else:
            print("[VOCAB] ⚠️ English vocabulary file not found")

        # ─── Arabic ───────────────────────────
        ar_path = vocab_dir / "ar_vocabulary.json"
        if ar_path.exists():
            with open(ar_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.ar_corrections = data.get("corrections", {})
                self.ar_metadata    = data.get("_metadata", {})
            print(
                f"[VOCAB] Arabic loaded ✅ "
                f"({len(self.ar_corrections)} corrections) "
                f"v{self.ar_metadata.get('version', '?')}"
            )
        else:
            print("[VOCAB] ⚠️ Arabic vocabulary file not found")

    # ─────────────────────────────────────────
    # MAIN CORRECT METHOD
    # ─────────────────────────────────────────
    def correct(self, text: str, language: str = "en") -> str:
        """
        Apply vocabulary corrections to transcribed text.

        Args:
            text: Raw Whisper transcription
            language: 'en' or 'ar'

        Returns:
            Corrected text
        """
        if not text:
            return text

        original = text
        corrections = (
            self.en_corrections if language == "en"
            else self.ar_corrections
        )

        if language == "en":
            corrected = self._correct_english(text, corrections)
        else:
            corrected = self._correct_arabic(text, corrections)

        if corrected != original:
            print(f"[VOCAB] Corrected: '{original}' → '{corrected}'")

        return corrected

    # ─────────────────────────────────────────
    # ENGLISH CORRECTION
    # Case-insensitive, whole phrase matching
    # ─────────────────────────────────────────
    def _correct_english(self, text: str, corrections: dict) -> str:
        """Apply English corrections — case insensitive."""
        result = text

        # Sort by length (longest first) to avoid partial replacements
        sorted_corrections = sorted(
            corrections.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        text_lower = result.lower()

        for wrong, correct in sorted_corrections:
            wrong_lower = wrong.lower()
            if wrong_lower in text_lower:
                # Case-insensitive replace preserving surrounding text
                pattern = re.compile(re.escape(wrong), re.IGNORECASE)
                result = pattern.sub(correct, result)
                text_lower = result.lower()

        # ─── Capitalize first letter ──────────
        if result:
            result = result[0].upper() + result[1:]

        return result.strip()

    # ─────────────────────────────────────────
    # ARABIC CORRECTION
    # Direct string matching for Arabic
    # ─────────────────────────────────────────
    def _correct_arabic(self, text: str, corrections: dict) -> str:
        """Apply Arabic corrections."""
        result = text

        sorted_corrections = sorted(
            corrections.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for wrong, correct in sorted_corrections:
            if wrong in result:
                result = result.replace(wrong, correct)

        return result.strip()

    # ─────────────────────────────────────────
    # RELOAD (after vocabulary update)
    # ─────────────────────────────────────────
    def reload(self):
        """Reload vocabulary files after update."""
        self._load_vocabularies()
        print("[VOCAB] Vocabulary reloaded ✅")

    # ─── Stats ────────────────────────────────
    def get_stats(self) -> dict:
        return {
            "en_corrections": len(self.en_corrections),
            "ar_corrections": len(self.ar_corrections),
            "en_version":     self.en_metadata.get("version", "?"),
            "ar_version":     self.ar_metadata.get("version", "?"),
        }


# ─── Singleton Instance ───────────────────────
corrector = VocabularyCorrector()