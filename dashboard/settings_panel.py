# ─────────────────────────────────────────────
# SETTINGS PANEL — Dashboard configuration UI
# Matches reference image layout exactly
# Robot Name, Identity, Enterprise Info, Style
# ─────────────────────────────────────────────

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QScrollArea,
    QFrame, QComboBox, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.config_manager import config


class SettingsPanel(QWidget):

    # ─── Signal emitted when settings saved ───
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_current_values()

    # ─────────────────────────────────────────
    # SETUP UI
    # ─────────────────────────────────────────
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ─── Scroll Area ──────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #1A1A2E;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #00D4FF;
                border-radius: 3px;
            }
        """)

        # ─── Scroll Content ───────────────────
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(40, 30, 40, 30)
        self.content_layout.setSpacing(30)

        # ─── Build Sections ───────────────────
        self._build_basic_info_section()
        self._build_conversation_style_section()
        self._build_ui_section()
        self._build_save_button()

        self.content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ─────────────────────────────────────────
    # SECTION: BASIC INFORMATION
    # ─────────────────────────────────────────
    def _build_basic_info_section(self):
        self.content_layout.addWidget(
            self._section_title("Basic Information")
        )

        # ─── Robot Name ───────────────────────
        self.content_layout.addWidget(
            self._field_label("Robot Name", required=True)
        )
        self.robot_name_input = self._create_line_edit(
            placeholder="e.g. Alexa",
            max_length=30
        )
        self.robot_name_counter = self._create_counter("0 / 30")
        self.robot_name_input.textChanged.connect(
            lambda t: self.robot_name_counter.setText(
                f"{len(t)} / 30"
            )
        )
        self.content_layout.addWidget(self.robot_name_input)
        self.content_layout.addWidget(self.robot_name_counter)
        self.content_layout.addWidget(
            self._field_hint(
                "This is the robot's public display name, "
                "recommended to be concise and memorable."
            )
        )

        # ─── Robot Identity ───────────────────
        self.content_layout.addWidget(
            self._field_label("Robot Identity / Role", required=True)
        )
        self.robot_identity_input = self._create_text_edit(
            placeholder=(
                "e.g. Alexa is an autonomous reception and visitor "
                "management robot that automates front-desk operations..."
            ),
            max_height=120
        )
        self.robot_identity_counter = self._create_counter("0 / 2000")
        self.robot_identity_input.textChanged.connect(
            lambda: self.robot_identity_counter.setText(
                f"{len(self.robot_identity_input.toPlainText())} / 2000"
            )
        )
        self.content_layout.addWidget(self.robot_identity_input)
        self.content_layout.addWidget(self.robot_identity_counter)
        self.content_layout.addWidget(
            self._field_hint(
                "A description of what the robot does and the role it plays."
            )
        )

        # ─── Service Enterprise Introduction ──
        self.content_layout.addWidget(
            self._field_label(
                "Service Enterprise Introduction", required=True
            )
        )
        self.enterprise_intro_input = self._create_text_edit(
            placeholder=(
                "Introduce the company/venue this robot represents. "
                "Used when visitors ask 'Who are you?' or "
                "'Tell me about yourselves'."
            ),
            max_height=150
        )
        self.enterprise_intro_counter = self._create_counter("0 / 900")
        self.enterprise_intro_input.textChanged.connect(
            lambda: self.enterprise_intro_counter.setText(
                f"{len(self.enterprise_intro_input.toPlainText())} / 900"
            )
        )
        self.content_layout.addWidget(self.enterprise_intro_input)
        self.content_layout.addWidget(self.enterprise_intro_counter)
        self.content_layout.addWidget(
            self._field_hint(
                "Objectively introduce the venue/enterprise. Used to answer "
                "'Who are you / Tell me about yourselves'."
            )
        )

        # ─── Additional Information ───────────
        self.content_layout.addWidget(
            self._field_label("Additional Information (Optional)")
        )
        self.additional_info_input = self._create_text_edit(
            placeholder=(
                "Optional additional knowledge for the robot. "
                "e.g. location details, special instructions, FAQs..."
            ),
            max_height=150
        )
        self.additional_info_counter = self._create_counter("0 / 8000")
        self.additional_info_input.textChanged.connect(
            lambda: self.additional_info_counter.setText(
                f"{len(self.additional_info_input.toPlainText())} / 8000"
            )
        )
        self.content_layout.addWidget(self.additional_info_input)
        self.content_layout.addWidget(self.additional_info_counter)
        self.content_layout.addWidget(
            self._field_hint(
                "Optional field for supplemental knowledge. "
                "Helps robot answer specific questions accurately."
            )
        )

    # ─────────────────────────────────────────
    # SECTION: CONVERSATION STYLE
    # ─────────────────────────────────────────
    def _build_conversation_style_section(self):
        self.content_layout.addWidget(
            self._section_title("Conversation Style")
        )

        styles_widget = QWidget()
        styles_layout = QHBoxLayout(styles_widget)
        styles_layout.setContentsMargins(0, 0, 0, 0)
        styles_layout.setSpacing(12)

        # ─── Style Checkboxes ─────────────────
        self.style_checks = {}
        styles = [
            "Conversational", "Natural", "Friendly",
            "Professional", "Formal", "Concise"
        ]

        for style in styles:
            cb = QCheckBox(style)
            cb.setStyleSheet("""
                QCheckBox {
                    color: #CCCCCC;
                    font-size: 13px;
                    padding: 6px 12px;
                    border: 1px solid #333355;
                    border-radius: 16px;
                    background: #1A1A2E;
                }
                QCheckBox:checked {
                    color: #0A0A1A;
                    background: #00D4FF;
                    border-color: #00D4FF;
                }
                QCheckBox::indicator { width: 0; height: 0; }
            """)
            self.style_checks[style] = cb
            styles_layout.addWidget(cb)

        styles_layout.addStretch()
        self.content_layout.addWidget(styles_widget)

    # ─────────────────────────────────────────
    # SECTION: UI CUSTOMIZATION
    # ─────────────────────────────────────────
    def _build_ui_section(self):
        self.content_layout.addWidget(
            self._section_title("UI Customization")
        )

        # ─── Show Subtitles Toggle ────────────
        self.show_subtitles_cb = QCheckBox("Show live subtitles on robot screen")
        self.show_subtitles_cb.setStyleSheet("""
            QCheckBox {
                color: #CCCCCC;
                font-size: 14px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border: 2px solid #333355;
                border-radius: 4px;
                background: #1A1A2E;
            }
            QCheckBox::indicator:checked {
                background: #00D4FF;
                border-color: #00D4FF;
            }
        """)
        self.show_subtitles_cb.setChecked(True)
        self.content_layout.addWidget(self.show_subtitles_cb)

        # ─── Primary Color ────────────────────
        self.content_layout.addWidget(
            self._field_label("Primary Accent Color")
        )
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(10)

        colors = [
            ("#00D4FF", "Cyan"),
            ("#7B2FBE", "Purple"),
            ("#00FF88", "Green"),
            ("#FF6B9D", "Pink"),
            ("#FFB800", "Gold"),
        ]

        self.color_buttons = {}
        for hex_color, name in colors:
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setToolTip(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_color};
                    border-radius: 18px;
                    border: 3px solid transparent;
                }}
                QPushButton:hover {{
                    border: 3px solid white;
                }}
            """)
            btn.clicked.connect(
                lambda checked, c=hex_color: self._select_color(c)
            )
            self.color_buttons[hex_color] = btn
            color_layout.addWidget(btn)

        color_layout.addStretch()
        self.content_layout.addWidget(color_widget)

    # ─── Color Selection ──────────────────────
    def _select_color(self, hex_color: str):
        """Highlight selected color button."""
        for color, btn in self.color_buttons.items():
            border = "white" if color == hex_color else "transparent"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    border-radius: 18px;
                    border: 3px solid {border};
                }}
                QPushButton:hover {{ border: 3px solid white; }}
            """)
        self.selected_color = hex_color

    # ─────────────────────────────────────────
    # SAVE BUTTON
    # ─────────────────────────────────────────
    def _build_save_button(self):
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 20, 0, 0)

        self.save_btn = QPushButton("💾  Save Configuration")
        self.save_btn.setFixedHeight(52)
        self.save_btn.setMinimumWidth(220)
        self.save_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D4FF, stop:1 #7B2FBE
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 40px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00BBEE, stop:1 #6A1FAD
                );
            }
            QPushButton:pressed { opacity: 0.8; }
        """)
        self.save_btn.clicked.connect(self._save_settings)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(btn_widget)

    # ─────────────────────────────────────────
    # LOAD CURRENT VALUES
    # ─────────────────────────────────────────
    def _load_current_values(self):
        """Populate fields with current config values."""
        self.robot_name_input.setText(
            config.get("robot", "name", default="Alexa")
        )
        self.robot_identity_input.setPlainText(
            config.get("identity", "robot_identity", default="")
        )
        self.enterprise_intro_input.setPlainText(
            config.get("identity", "enterprise_introduction", default="")
        )
        self.additional_info_input.setPlainText(
            config.get("identity", "additional_information", default="")
        )

        # ─── Conversation styles ──────────────
        saved_styles = config.get(
            "robot", "conversation_style", default=["Friendly"]
        )
        for style, cb in self.style_checks.items():
            cb.setChecked(style in saved_styles)

        # ─── UI settings ─────────────────────
        self.show_subtitles_cb.setChecked(
            config.get("ui", "show_subtitles", default=True)
        )
        self.selected_color = config.get(
            "ui", "primary_color", default="#00D4FF"
        )
        self._select_color(self.selected_color)

    # ─────────────────────────────────────────
    # SAVE SETTINGS
    # ─────────────────────────────────────────
    def _save_settings(self):
        """Save all settings to config."""

        # ─── Robot Info ───────────────────────
        config.set(
            self.robot_name_input.text().strip(),
            "robot", "name"
        )
        config.set(
            self.robot_identity_input.toPlainText().strip(),
            "identity", "robot_identity"
        )
        config.set(
            self.enterprise_intro_input.toPlainText().strip(),
            "identity", "enterprise_introduction"
        )
        config.set(
            self.additional_info_input.toPlainText().strip(),
            "identity", "additional_information"
        )

        # ─── Conversation Style ───────────────
        selected_styles = [
            style for style, cb in self.style_checks.items()
            if cb.isChecked()
        ]
        if not selected_styles:
            selected_styles = ["Friendly"]
        config.set(selected_styles, "robot", "conversation_style")

        # ─── UI Settings ─────────────────────
        config.set(
            self.show_subtitles_cb.isChecked(),
            "ui", "show_subtitles"
        )
        config.set(self.selected_color, "ui", "primary_color")

        # ─── Notify AI brain to reload ────────
        try:
            from core.ai_brain import ai_brain
            ai_brain.reload_config()
        except Exception:
            pass

        # ─── Visual feedback ──────────────────
        self.save_btn.setText("✅  Saved Successfully!")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #00AA44;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 40px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(
            2000, self._reset_save_button
        )
        self.settings_saved.emit()
        print("[DASHBOARD] Settings saved ✅")

    # ─── Reset Save Button ────────────────────
    def _reset_save_button(self):
        self.save_btn.setText("💾  Save Configuration")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D4FF, stop:1 #7B2FBE
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 40px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00BBEE, stop:1 #6A1FAD
                );
            }
        """)

    # ─────────────────────────────────────────
    # UI HELPER WIDGETS
    # ─────────────────────────────────────────
    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        label.setStyleSheet("""
            color: #00D4FF;
            padding-top: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid rgba(0,212,255,0.2);
        """)
        return label

    def _field_label(self, text: str, required=False) -> QLabel:
        star = ' <span style="color:#FF4444;">*</span>' if required else ""
        label = QLabel(f"{text}{star}")
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        label.setStyleSheet("color: #00D4FF; margin-top: 8px;")
        return label

    def _field_hint(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #555577; font-size: 12px; margin-bottom: 5px;")
        return label

    def _create_counter(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        label.setStyleSheet("color: #444466; font-size: 12px;")
        return label

    def _create_line_edit(self, placeholder="", max_length=100) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMaxLength(max_length)
        field.setFixedHeight(44)
        field.setStyleSheet("""
            QLineEdit {
                background: #1A1A2E;
                border: 1px solid #2A2A4A;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 0 15px;
            }
            QLineEdit:focus {
                border: 1px solid #00D4FF;
            }
        """)
        return field

    def _create_text_edit(self, placeholder="", max_height=120) -> QTextEdit:
        field = QTextEdit()
        field.setPlaceholderText(placeholder)
        field.setMaximumHeight(max_height)
        field.setStyleSheet("""
            QTextEdit {
                background: #1A1A2E;
                border: 1px solid #2A2A4A;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 10px 15px;
            }
            QTextEdit:focus {
                border: 1px solid #00D4FF;
            }
        """)
        return field