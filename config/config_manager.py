# ─────────────────────────────────────────────
# CONFIG MANAGER — Handles all app configuration
# Loads, saves, and provides access to settings
# ─────────────────────────────────────────────

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# ─── Load environment variables ───────────────
load_dotenv()

# ─── Paths ────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "default_config.json"
USER_CONFIG_PATH = BASE_DIR / "config" / "user_config.json"


class ConfigManager:
    """
    Central configuration manager for ARIA robot.
    Merges default config with user overrides.
    Provides easy get/set access to all settings.
    """

    # ─── Initialize ───────────────────────────
    def __init__(self):
        self.config = {}
        self._load_config()

    # ─── Load Config ──────────────────────────
    def _load_config(self):
        """Load default config, then overlay user config if exists."""

        # Load default config
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Overlay user config if exists
        if USER_CONFIG_PATH.exists():
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                self._deep_merge(self.config, user_config)

    # ─── Deep Merge ───────────────────────────
    def _deep_merge(self, base: dict, override: dict):
        """Recursively merge override into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # ─── Get Value ────────────────────────────
    def get(self, *keys, default=None):
        """
        Get a config value by key path.
        Example: config.get("ui", "primary_color")
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    # ─── Set Value ────────────────────────────
    def set(self, value, *keys):
        """
        Set a config value by key path and save.
        Example: config.set("#FF0000", "ui", "primary_color")
        """
        d = self.config
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        self._save_user_config()

    # ─── Save User Config ─────────────────────
    def _save_user_config(self):
        """Save current config as user override file."""
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    # ─── API Keys (from .env) ─────────────────
    @property
    def gemini_api_key(self):
        return os.getenv("GEMINI_API_KEY", "")

    # ─── AI Provider ──────────────────────────
    @property
    def ai_provider(self):
        return os.getenv("AI_PROVIDER", "groq").lower()

    @property
    def openai_api_key(self):
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def groq_api_key(self):
        return os.getenv("GROQ_API_KEY", "")

    @property
    def gemini_api_key(self):
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def active_api_key(self):
        """Returns the currently active API key based on provider."""
        keys = {
            "openai": self.openai_api_key,
            "groq":   self.groq_api_key,
            "gemini": self.gemini_api_key,
        }
        return keys.get(self.ai_provider, "")

    @property
    def robot_name(self):
        return self.get("robot", "name", default="Aria")

    @property
    def wake_word(self):
        return self.get("robot", "wake_word", default="hey aria")

    @property
    def voice_english(self):
        return self.get("voices", "english", default="en-US-AriaNeural")

    @property
    def voice_arabic(self):
        return self.get("voices", "arabic", default="ar-OM-AbdullahNeural")


# ─── Singleton Instance ───────────────────────
config = ConfigManager()