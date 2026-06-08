from datetime import datetime, date, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.conversation_logger import conversation_logger


def _friendly_date(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = date.today()
        if d == today:
            return f"Today — {d.strftime('%B %d, %Y')}"
        if d == today - timedelta(days=1):
            return f"Yesterday — {d.strftime('%B %d, %Y')}"
        return d.strftime("%A, %B %d, %Y")
    except ValueError:
        return date_str


class _ExchangeCard(QWidget):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("exchangeCard")
        self._build(entry)

    def _build(self, entry: dict):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        # ── timestamp row ──
        time_lbl = QLabel(entry.get("time", ""))
        time_lbl.setObjectName("cardTime")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_lbl.setFont(QFont("Segoe UI", 9))
        layout.addWidget(time_lbl)

        # ── user row ──
        layout.addWidget(self._msg_row("YOU", entry.get("user", ""), "#5CF5A1", "#A8D5A8"))

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("cardSep")
        layout.addWidget(sep)

        # ── assistant row ──
        lang = entry.get("language", "en")
        name = "ARIA"
        layout.addWidget(self._msg_row(name, entry.get("assistant", ""), "#53E6FF", "#C8E8FF"))

    def _msg_row(self, label: str, text: str, label_color: str, text_color: str) -> QWidget:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        hl.setAlignment(Qt.AlignmentFlag.AlignTop)

        tag = QLabel(label)
        tag.setObjectName("msgTag")
        tag.setFixedWidth(38)
        tag.setFont(QFont("Segoe UI Semibold", 8))
        tag.setStyleSheet(f"color: {label_color}; letter-spacing: 2px;")
        tag.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setFont(QFont("Segoe UI", 12))
        body.setStyleSheet(f"color: {text_color};")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        hl.addWidget(tag)
        hl.addWidget(body, 1)
        return row


class _DateSection(QWidget):
    def __init__(self, date_str: str, entries: list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(8)

        # date header
        hdr = QLabel(_friendly_date(date_str))
        hdr.setObjectName("dateHeader")
        hdr.setFont(QFont("Segoe UI Semibold", 10))
        layout.addWidget(hdr)

        for entry in entries:
            layout.addWidget(_ExchangeCard(entry))


class ConversationPanel(QWidget):
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_style()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        # ── header bar ──
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)

        title = QLabel("Conversation History")
        title.setObjectName("panelTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("histRefreshBtn")
        self._refresh_btn.setFixedHeight(36)
        self._refresh_btn.setFont(QFont("Segoe UI Semibold", 10))
        self._refresh_btn.clicked.connect(self.refresh)

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setObjectName("histClearBtn")
        self._clear_btn.setFixedHeight(36)
        self._clear_btn.setFont(QFont("Segoe UI Semibold", 10))
        self._clear_btn.clicked.connect(self._on_clear)

        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(self._refresh_btn)
        hl.addWidget(self._clear_btn)
        root.addWidget(header)

        # ── scroll area ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setObjectName("histScroll")

        self._content = QWidget()
        self._content.setObjectName("histContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 8, 0)
        self._content_layout.setSpacing(20)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

    def refresh(self):
        # Clear existing content (keep the trailing stretch)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = conversation_logger.load_all()

        if not history:
            empty = QLabel("No conversations recorded yet.")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Segoe UI", 13))
            self._content_layout.insertWidget(0, empty)
            return

        # Sort dates newest-first; display sections top→bottom (newest at top)
        for date_str in sorted(history.keys(), reverse=True):
            entries = history[date_str]
            section = _DateSection(date_str, entries)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, section
            )

    def _on_clear(self):
        conversation_logger.clear_all()
        self.refresh()

    def _apply_style(self):
        self.setStyleSheet(
            """
            QWidget { background: transparent; color: #F4F8FF; }

            #panelTitle { color: #F4F8FF; }

            #histRefreshBtn {
                background: rgba(83, 230, 255, 0.08);
                color: #53E6FF;
                border: 1px solid rgba(83, 230, 255, 0.28);
                border-radius: 10px;
                padding: 0 14px;
            }
            #histRefreshBtn:hover { background: rgba(83, 230, 255, 0.16); }

            #histClearBtn {
                background: rgba(255, 100, 100, 0.08);
                color: #FF7070;
                border: 1px solid rgba(255, 100, 100, 0.28);
                border-radius: 10px;
                padding: 0 14px;
            }
            #histClearBtn:hover { background: rgba(255, 100, 100, 0.16); }

            #histScroll {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.03);
                width: 7px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(83,230,255,0.35);
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

            #histContent { background: transparent; }

            #dateHeader {
                color: #53E6FF;
                letter-spacing: 2px;
                padding: 6px 0 2px 2px;
            }

            #exchangeCard {
                background: rgba(10, 17, 31, 0.82);
                border: 1px solid rgba(83, 230, 255, 0.10);
                border-radius: 18px;
            }

            #cardTime { color: #5A7499; }

            #cardSep { background: rgba(255,255,255,0.07); }

            #emptyLabel { color: #5A7499; }
            """
        )
