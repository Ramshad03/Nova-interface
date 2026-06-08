from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config.config_manager import config


class UISettingsPanel(QWidget):
    settings_saved = pyqtSignal()

    # ── voice options ─────────────────────────────────────────────────
    EN_VOICES = [
        ("en-US-AriaNeural",    "Aria — US Female"),
        ("en-US-GuyNeural",     "Guy — US Male"),
        ("en-GB-SoniaNeural",   "Sonia — UK Female"),
        ("en-GB-RyanNeural",    "Ryan — UK Male"),
        ("en-AU-NatashaNeural", "Natasha — AU Female"),
    ]
    AR_VOICES = [
        ("ar-OM-AbdullahNeural", "Abdullah — Oman Male"),
        ("ar-SA-ZariyahNeural",  "Zariyah — Saudi Female"),
        ("ar-AE-FatimaNeural",   "Fatima — UAE Female"),
        ("ar-EG-ShakirNeural",   "Shakir — Egypt Male"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_stylesheet()
        self._load_values()

    # ─────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("uiScroll")

        content = QWidget()
        content.setObjectName("uiContent")
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(34, 34, 34, 34)
        self._cl.setSpacing(24)

        self._build_display_section()
        self._build_ai_section()
        self._build_audio_section()
        self._build_save_bar()

        self._cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    # ── Display ───────────────────────────────────────────────────────

    def _build_display_section(self):
        card, lay = self._card("Display", "Subtitle visibility, accent color, and orb animation speed.")

        self.show_subtitles_cb = QCheckBox("Show live subtitles on the robot screen")
        self.show_subtitles_cb.setObjectName("uiToggle")
        lay.addWidget(self.show_subtitles_cb)

        lay.addSpacing(10)
        lay.addWidget(self._label("Accent Color"))
        lay.addWidget(self._hint("Affects the orb, status bar, and UI highlights."))

        color_row = QWidget()
        cr = QHBoxLayout(color_row)
        cr.setContentsMargins(0, 4, 0, 0)
        cr.setSpacing(10)
        colors = [
            ("#53E6FF", "Cyan"),
            ("#9C5BFF", "Violet"),
            ("#5CF5A1", "Mint"),
            ("#FF7AB6", "Pink"),
            ("#FFD166", "Amber"),
        ]
        self._color_btns: dict = {}
        self._selected_color = "#53E6FF"
        for hex_val, name in colors:
            btn = QPushButton(name)
            btn.setObjectName("colorChip")
            btn.setFixedHeight(40)
            btn.setProperty("chipColor", hex_val)
            btn.clicked.connect(lambda _, h=hex_val: self._pick_color(h))
            self._color_btns[hex_val] = btn
            cr.addWidget(btn)
        cr.addStretch()
        lay.addWidget(color_row)

        lay.addSpacing(10)
        lay.addWidget(self._label("Animation Speed"))
        lay.addWidget(self._hint("Controls how fast the orb pulses and rings animate."))
        self.anim_slider, anim_val_lbl = self._slider(5, 20, 10, lambda v: f"{v / 10:.1f}×")
        self._anim_val_lbl = anim_val_lbl
        lay.addWidget(self._slider_row("0.5×", self.anim_slider, "2.0×", anim_val_lbl))

        self._cl.addWidget(card)

    # ── AI Behaviour ──────────────────────────────────────────────────

    def _build_ai_section(self):
        card, lay = self._card(
            "AI Behaviour",
            "Control how the AI responds — length, creativity, and memory depth.",
        )

        lay.addWidget(self._label("Response Length"))
        lay.addWidget(self._hint("Higher values allow longer answers. Keep low for a kiosk."))
        self.tokens_slider, self._tokens_val = self._slider(60, 400, 120, lambda v: f"{v} tokens", step=20)
        lay.addWidget(self._slider_row("60", self.tokens_slider, "400", self._tokens_val))

        lay.addSpacing(10)
        lay.addWidget(self._label("Creativity (Temperature)"))
        lay.addWidget(self._hint("Low = focused and factual.  High = more varied and expressive."))
        self.temp_slider, self._temp_val = self._slider(1, 10, 5, lambda v: f"{v / 10:.1f}")
        lay.addWidget(self._slider_row("0.1", self.temp_slider, "1.0", self._temp_val))

        lay.addSpacing(10)
        lay.addWidget(self._label("Conversation Memory"))
        lay.addWidget(self._hint("How many previous turns the AI remembers per session."))
        self.memory_slider, self._memory_val = self._slider(2, 20, 10, lambda v: f"{v} turns", step=2)
        lay.addWidget(self._slider_row("2", self.memory_slider, "20", self._memory_val))

        self._cl.addWidget(card)

    # ── Audio & Voice ─────────────────────────────────────────────────

    def _build_audio_section(self):
        card, lay = self._card(
            "Audio & Voice",
            "Choose TTS voices and the Whisper model used for local speech fallback.",
        )

        lay.addWidget(self._label("English Voice"))
        self.en_voice_cb = self._combo([(v, l) for v, l in self.EN_VOICES])
        lay.addWidget(self.en_voice_cb)

        lay.addSpacing(10)
        lay.addWidget(self._label("Arabic Voice"))
        self.ar_voice_cb = self._combo([(v, l) for v, l in self.AR_VOICES])
        lay.addWidget(self.ar_voice_cb)

        lay.addSpacing(10)
        lay.addWidget(self._label("Local Whisper Model"))
        lay.addWidget(
            self._hint(
                "Used when Groq is unavailable. Larger models are more accurate but slower to load."
            )
        )
        self.whisper_cb = self._combo([
            ("tiny",   "Tiny  — fastest, least accurate"),
            ("base",   "Base  — good balance"),
            ("small",  "Small — slower, more accurate"),
            ("medium", "Medium — high accuracy"),
        ])
        lay.addWidget(self.whisper_cb)

        self._cl.addWidget(card)

    # ── Save bar ──────────────────────────────────────────────────────

    def _build_save_bar(self):
        bar = QFrame()
        bar.setObjectName("uiActionBar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 20, 24, 20)

        hint = QLabel("Changes take effect after saving. Voice changes apply on next response.")
        hint.setObjectName("uiSaveHint")
        hint.setFont(QFont("Segoe UI", 10))

        self._save_btn = QPushButton("Save UI Settings")
        self._save_btn.setFixedHeight(52)
        self._save_btn.setMinimumWidth(210)
        self._save_btn.setFont(QFont("Segoe UI Semibold", 11))
        self._save_btn.setObjectName("uiSaveBtn")
        self._save_btn.clicked.connect(self._save)

        bl.addWidget(hint)
        bl.addStretch()
        bl.addWidget(self._save_btn)
        self._cl.addWidget(bar)

    # ─────────────────────────────────────────────────────────────────
    # LOAD / SAVE
    # ─────────────────────────────────────────────────────────────────

    def _load_values(self):
        self.show_subtitles_cb.setChecked(
            config.get("ui", "show_subtitles", default=True)
        )

        color = config.get("ui", "primary_color", default="#53E6FF")
        self._pick_color(color)

        speed = config.get("ui", "animation_speed", default=1.0)
        self.anim_slider.setValue(int(round(speed * 10)))
        self._anim_val_lbl.setText(f"{speed:.1f}×")

        tokens = config.get("ai", "max_tokens", default=120)
        self.tokens_slider.setValue(int(tokens))
        self._tokens_val.setText(f"{tokens} tokens")

        temp = config.get("ai", "temperature", default=0.5)
        self.temp_slider.setValue(int(round(temp * 10)))
        self._temp_val.setText(f"{temp:.1f}")

        memory = config.get("ai", "context_memory", default=10)
        self.memory_slider.setValue(int(memory))
        self._memory_val.setText(f"{memory} turns")

        en_voice = config.get("voices", "english", default="en-US-AriaNeural")
        self._set_combo(self.en_voice_cb, en_voice)

        ar_voice = config.get("voices", "arabic", default="ar-OM-AbdullahNeural")
        self._set_combo(self.ar_voice_cb, ar_voice)

        whisper = config.get("audio", "whisper_model", default="tiny")
        self._set_combo(self.whisper_cb, whisper)

    def _save(self):
        config.set(self.show_subtitles_cb.isChecked(), "ui", "show_subtitles")
        config.set(self._selected_color, "ui", "primary_color")
        config.set(round(self.anim_slider.value() / 10, 1), "ui", "animation_speed")

        config.set(self.tokens_slider.value(), "ai", "max_tokens")
        config.set(round(self.temp_slider.value() / 10, 1), "ai", "temperature")
        config.set(self.memory_slider.value(), "ai", "context_memory")

        config.set(self.en_voice_cb.currentData(), "voices", "english")
        config.set(self.ar_voice_cb.currentData(), "voices", "arabic")
        config.set(self.whisper_cb.currentData(), "audio", "whisper_model")

        # Apply voice changes live to the running TTS engine
        try:
            from core.tts_engine import tts
            tts.VOICES["en"] = self.en_voice_cb.currentData()
            tts.VOICES["ar"] = self.ar_voice_cb.currentData()
        except Exception:
            pass

        # Reload Whisper model in background if it changed
        try:
            from core.stt_engine import stt
            stt.reload_model()
        except Exception:
            pass

        self._save_btn.setText("Saved!")
        self._save_btn.setObjectName("uiSaveBtnOk")
        self._save_btn.style().unpolish(self._save_btn)
        self._save_btn.style().polish(self._save_btn)
        QTimer.singleShot(2000, self._reset_btn)
        self.settings_saved.emit()

    def _reset_btn(self):
        self._save_btn.setText("Save UI Settings")
        self._save_btn.setObjectName("uiSaveBtn")
        self._save_btn.style().unpolish(self._save_btn)
        self._save_btn.style().polish(self._save_btn)

    # ─────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────

    def _pick_color(self, hex_val: str):
        self._selected_color = hex_val
        for h, btn in self._color_btns.items():
            active = h == hex_val
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {'rgba(255,255,255,0.09)' if active else 'rgba(255,255,255,0.03)'};
                    color: {'#F4F8FF' if active else '#8CA2C3'};
                    border: 1px solid {h if active else 'rgba(255,255,255,0.09)'};
                    border-radius: 14px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.07); }}
                """
            )

    def _slider(self, mn, mx, default, fmt_fn, step=1):
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(mn, mx)
        sl.setValue(default)
        sl.setSingleStep(step)
        sl.setPageStep(step)
        sl.setObjectName("uiSlider")

        val_lbl = QLabel(fmt_fn(default))
        val_lbl.setObjectName("sliderVal")
        val_lbl.setFixedWidth(80)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setFont(QFont("Segoe UI Semibold", 10))

        sl.valueChanged.connect(lambda v: val_lbl.setText(fmt_fn(v)))
        return sl, val_lbl

    def _slider_row(self, left_lbl: str, slider: QSlider, right_lbl: str, val_lbl: QLabel) -> QWidget:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)

        def _edge(text):
            l = QLabel(text)
            l.setObjectName("sliderEdge")
            l.setFont(QFont("Segoe UI", 9))
            l.setFixedWidth(34)
            return l

        hl.addWidget(_edge(left_lbl))
        hl.addWidget(slider, 1)
        hl.addWidget(_edge(right_lbl))
        hl.addWidget(val_lbl)
        return row

    def _combo(self, items: list) -> QComboBox:
        cb = QComboBox()
        cb.setObjectName("uiCombo")
        cb.setFixedHeight(46)
        cb.setFont(QFont("Segoe UI", 11))
        for value, label in items:
            cb.addItem(label, userData=value)
        return cb

    def _set_combo(self, cb: QComboBox, value: str):
        for i in range(cb.count()):
            if cb.itemData(i) == value:
                cb.setCurrentIndex(i)
                return

    def _card(self, title: str, desc: str):
        card = QFrame()
        card.setObjectName("uiCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(10)

        h = QLabel(title)
        h.setObjectName("uiCardTitle")
        h.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        d = QLabel(desc)
        d.setObjectName("uiCardDesc")
        d.setWordWrap(True)
        d.setFont(QFont("Segoe UI", 10))

        lay.addWidget(h)
        lay.addWidget(d)
        lay.addSpacing(6)
        return card, lay

    def _label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName("uiFieldLabel")
        l.setFont(QFont("Segoe UI Semibold", 11))
        return l

    def _hint(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName("uiFieldHint")
        l.setWordWrap(True)
        l.setFont(QFont("Segoe UI", 9))
        return l

    # ─────────────────────────────────────────────────────────────────
    # STYLESHEET
    # ─────────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            #uiContent { background: transparent; }
            #uiScroll  { border: none; background: transparent; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.03); width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(83,230,255,0.45); border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

            #uiCard, #uiActionBar {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 24px;
            }
            #uiCardTitle { color: #F4F8FF; }
            #uiCardDesc  { color: #8CA2C3; }

            #uiFieldLabel { color: #DCE9FF; margin-top: 4px; }
            #uiFieldHint  { color: #7F98B9; }

            #uiToggle {
                color: #E8F0FF;
                font-size: 13px;
                spacing: 10px;
            }
            #uiToggle::indicator {
                width: 20px; height: 20px;
                border: 2px solid rgba(255,255,255,0.14);
                border-radius: 6px;
                background: rgba(8,14,27,0.90);
            }
            #uiToggle::indicator:checked {
                background: #53E6FF; border-color: #53E6FF;
            }

            #uiSlider::groove:horizontal {
                height: 6px;
                background: rgba(255,255,255,0.08);
                border-radius: 3px;
            }
            #uiSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #53E6FF, stop:1 #4A7DFF);
                border-radius: 3px;
            }
            #uiSlider::handle:horizontal {
                width: 18px; height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                background: #F4F8FF;
            }

            #sliderVal  { color: #53E6FF; }
            #sliderEdge { color: #5A7499; }

            #uiCombo {
                background: rgba(8,14,27,0.90);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 14px;
                color: #F4F8FF;
                padding: 0 14px;
            }
            #uiCombo:focus { border-color: rgba(83,230,255,0.55); }
            QComboBox::drop-down { border: none; width: 32px; }
            QComboBox QAbstractItemView {
                background: #0C1628;
                border: 1px solid rgba(83,230,255,0.18);
                border-radius: 12px;
                color: #F4F8FF;
                selection-background-color: rgba(83,230,255,0.18);
                padding: 4px;
            }

            #uiSaveHint { color: #7F98B9; }

            #uiSaveBtn, #uiSaveBtnOk {
                border: none;
                border-radius: 16px;
                padding: 0 24px;
                color: white;
            }
            #uiSaveBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #53E6FF, stop:1 #4A7DFF);
            }
            #uiSaveBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6BEAFF, stop:1 #618FFF);
            }
            #uiSaveBtnOk { background: #1FAA63; }
            """
        )
