import json
import threading
from datetime import datetime
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_HISTORY_FILE = _DATA_DIR / "conversation_history.json"


class ConversationLogger:
    """
    Persists every user↔assistant exchange to a local JSON file,
    keyed by ISO date so the dashboard can display day-wise history.

    File layout
    -----------
    {
      "2026-06-08": [
        { "time": "14:30:22", "user": "...", "assistant": "...", "language": "en" },
        ...
      ],
      ...
    }
    """

    def __init__(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(self, user_text: str, assistant_text: str, language: str = "en") -> None:
        user_text = (user_text or "").strip()
        assistant_text = (assistant_text or "").strip()
        if not user_text or not assistant_text:
            return

        now = datetime.now()
        entry = {
            "time": now.strftime("%H:%M:%S"),
            "user": user_text,
            "assistant": assistant_text,
            "language": language,
        }
        date_key = now.strftime("%Y-%m-%d")

        with self._lock:
            data = self._load()
            data.setdefault(date_key, []).append(entry)
            self._save(data)

    def load_all(self) -> dict:
        with self._lock:
            return self._load()

    def clear_all(self) -> None:
        with self._lock:
            self._save({})

    def _load(self) -> dict:
        if not _HISTORY_FILE.exists():
            return {}
        try:
            with open(_HISTORY_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)


conversation_logger = ConversationLogger()
