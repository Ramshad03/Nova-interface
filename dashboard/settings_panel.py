from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.config_manager import config


class SettingsPanel(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_color = "#00D4FF"
        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.03);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(83, 230, 255, 0.45);
                border-radius: 4px;
            }
            """
        )

        content = QWidget()
        content.setObjectName("settingsContent")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(34, 34, 34, 34)
        self.content_layout.setSpacing(24)

        self._build_basic_info_section()
        self._build_conversation_style_section()
        self._build_ui_section()
        self._build_save_button()

        self.content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self._apply_stylesheet()

    def _build_basic_info_section(self):
        section, layout = self._create_section_card(
            "Basic Information",
            "The same identity fields, presented with clearer grouping and spacing.",
        )

        layout.addWidget(self._field_label("Robot Name", required=True))
        self.robot_name_input = self._create_line_edit(
            placeholder="e.g. Alexa",
            max_length=30,
        )
        self.robot_name_counter = self._create_counter("0 / 30")
        self.robot_name_input.textChanged.connect(
            lambda text: self.robot_name_counter.setText(f"{len(text)} / 30")
        )
        layout.addWidget(self.robot_name_input)
        layout.addWidget(self.robot_name_counter)
        layout.addWidget(
            self._field_hint(
                "This is the robot's public display name and should stay concise."
            )
        )

        layout.addSpacing(8)
        layout.addWidget(
            self._field_label("Robot Identity / Role", required=True)
        )
        self.robot_identity_input = self._create_text_edit(
            placeholder=(
                "e.g. Alexa is an autonomous reception and visitor management robot "
                "that automates front-desk operations..."
            ),
            max_height=140,
        )
        self.robot_identity_counter = self._create_counter("0 / 2000")
        self.robot_identity_input.textChanged.connect(
            lambda: self.robot_identity_counter.setText(
                f"{len(self.robot_identity_input.toPlainText())} / 2000"
            )
        )
        layout.addWidget(self.robot_identity_input)
        layout.addWidget(self.robot_identity_counter)
        layout.addWidget(
            self._field_hint(
                "Describe the robot's purpose and role in a way visitors can understand."
            )
        )

        layout.addSpacing(8)
        layout.addWidget(
            self._field_label("Service Enterprise Introduction", required=True)
        )
        self.enterprise_intro_input = self._create_text_edit(
            placeholder=(
                "Introduce the company or venue this robot represents. "
                "This is used when visitors ask about the organization."
            ),
            max_height=150,
        )
        self.enterprise_intro_counter = self._create_counter("0 / 900")
        self.enterprise_intro_input.textChanged.connect(
            lambda: self.enterprise_intro_counter.setText(
                f"{len(self.enterprise_intro_input.toPlainText())} / 900"
            )
        )
        layout.addWidget(self.enterprise_intro_input)
        layout.addWidget(self.enterprise_intro_counter)
        layout.addWidget(
            self._field_hint(
                "Keep this introduction factual so the assistant can reuse it reliably."
            )
        )

        layout.addSpacing(8)
        layout.addWidget(
            self._field_label("Additional Information (Optional)")
        )
        self.additional_info_input = self._create_text_edit(
            placeholder=(
                "Optional knowledge such as location details, special instructions, or FAQs."
            ),
            max_height=170,
        )
        self.additional_info_counter = self._create_counter("0 / 8000")
        self.additional_info_input.textChanged.connect(
            lambda: self.additional_info_counter.setText(
                f"{len(self.additional_info_input.toPlainText())} / 8000"
            )
        )
        layout.addWidget(self.additional_info_input)
        layout.addWidget(self.additional_info_counter)
        layout.addWidget(
            self._field_hint(
                "Use this for supporting context that helps the assistant answer with more detail."
            )
        )

        self.content_layout.addWidget(section)

    def _build_conversation_style_section(self):
        section, layout = self._create_section_card(
            "Conversation Style",
            "These options still save the same way, but now read more like selectable chips.",
        )

        styles_widget = QWidget()
        styles_layout = QHBoxLayout(styles_widget)
        styles_layout.setContentsMargins(0, 0, 0, 0)
        styles_layout.setSpacing(10)

        self.style_checks = {}
        styles = [
            "Conversational",
            "Natural",
            "Friendly",
            "Professional",
            "Formal",
            "Concise",
        ]

        for style in styles:
            checkbox = QCheckBox(style)
            checkbox.setObjectName("styleChip")
            self.style_checks[style] = checkbox
            styles_layout.addWidget(checkbox)

        styles_layout.addStretch()
        layout.addWidget(styles_widget)
        self.content_layout.addWidget(section)

    def _build_ui_section(self):
        section, layout = self._create_section_card(
            "UI Customization",
            "Current display preferences are preserved and visually grouped for faster scanning.",
        )

        self.show_subtitles_cb = QCheckBox(
            "Show live subtitles on robot screen"
        )
        self.show_subtitles_cb.setObjectName("subtitlesToggle")
        self.show_subtitles_cb.setChecked(True)
        layout.addWidget(self.show_subtitles_cb)

        layout.addSpacing(12)
        layout.addWidget(self._field_label("Primary Accent Color"))

        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(12)

        colors = [
            ("#00D4FF", "Cyan"),
            ("#7B2FBE", "Purple"),
            ("#00FF88", "Green"),
            ("#FF6B9D", "Pink"),
            ("#FFB800", "Gold"),
        ]

        self.color_buttons = {}
        for hex_color, name in colors:
            button = QPushButton(name)
            button.setObjectName("colorChoice")
            button.setFixedHeight(42)
            button.clicked.connect(
                lambda checked, value=hex_color: self._select_color(value)
            )
            button.setProperty("accentColor", hex_color)
            self.color_buttons[hex_color] = button
            color_layout.addWidget(button)

        color_layout.addStretch()
        layout.addWidget(color_widget)
        self.content_layout.addWidget(section)

    def _build_save_button(self):
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 20, 24, 20)

        helper = QLabel("Changes are applied using the existing configuration flow.")
        helper.setObjectName("saveHelper")
        helper.setFont(QFont("Segoe UI", 10))

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setFixedHeight(52)
        self.save_btn.setMinimumWidth(220)
        self.save_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self._save_settings)

        action_layout.addWidget(helper)
        action_layout.addStretch()
        action_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(action_bar)

    def _load_current_values(self):
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

        saved_styles = config.get(
            "robot", "conversation_style", default=["Friendly"]
        )
        for style, checkbox in self.style_checks.items():
            checkbox.setChecked(style in saved_styles)

        self.show_subtitles_cb.setChecked(
            config.get("ui", "show_subtitles", default=True)
        )
        self.selected_color = config.get(
            "ui", "primary_color", default="#00D4FF"
        )
        self._select_color(self.selected_color)

        self.robot_name_counter.setText(
            f"{len(self.robot_name_input.text())} / 30"
        )
        self.robot_identity_counter.setText(
            f"{len(self.robot_identity_input.toPlainText())} / 2000"
        )
        self.enterprise_intro_counter.setText(
            f"{len(self.enterprise_intro_input.toPlainText())} / 900"
        )
        self.additional_info_counter.setText(
            f"{len(self.additional_info_input.toPlainText())} / 8000"
        )

    def _save_settings(self):
        config.set(self.robot_name_input.text().strip(), "robot", "name")
        config.set(
            self.robot_identity_input.toPlainText().strip(),
            "identity",
            "robot_identity",
        )
        config.set(
            self.enterprise_intro_input.toPlainText().strip(),
            "identity",
            "enterprise_introduction",
        )
        config.set(
            self.additional_info_input.toPlainText().strip(),
            "identity",
            "additional_information",
        )

        selected_styles = [
            style
            for style, checkbox in self.style_checks.items()
            if checkbox.isChecked()
        ]
        if not selected_styles:
            selected_styles = ["Friendly"]
        config.set(selected_styles, "robot", "conversation_style")

        config.set(
            self.show_subtitles_cb.isChecked(),
            "ui",
            "show_subtitles",
        )
        config.set(self.selected_color, "ui", "primary_color")

        try:
            from core.ai_brain import ai_brain

            ai_brain.reload_config()
        except Exception:
            pass

        self.save_btn.setText("Saved Successfully")
        self.save_btn.setObjectName("saveBtnSuccess")
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)

        QTimer.singleShot(2000, self._reset_save_button)
        self.settings_saved.emit()
        print("[DASHBOARD] Settings saved")

    def _reset_save_button(self):
        self.save_btn.setText("Save Configuration")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)

    def _select_color(self, hex_color: str):
        self.selected_color = hex_color
        for color, button in self.color_buttons.items():
            is_selected = color == hex_color
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.03);
                    color: #F4F8FF;
                    border: 1px solid {'rgba(255,255,255,0.1)' if not is_selected else hex_color};
                    border-radius: 14px;
                    padding: 0 16px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.06);
                }}
                """
            )

    def _create_section_card(self, title: str, description: str):
        card = QFrame()
        card.setObjectName("sectionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(10)

        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        heading.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        copy = QLabel(description)
        copy.setObjectName("sectionDescription")
        copy.setWordWrap(True)
        copy.setFont(QFont("Segoe UI", 10))

        layout.addWidget(heading)
        layout.addWidget(copy)
        layout.addSpacing(6)
        return card, layout

    def _field_label(self, text: str, required=False) -> QLabel:
        star = ' <span style="color:#FF7A7A;">*</span>' if required else ""
        label = QLabel(f"{text}{star}")
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setFont(QFont("Segoe UI Semibold", 11))
        label.setObjectName("fieldLabel")
        return label

    def _field_hint(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName("fieldHint")
        label.setFont(QFont("Segoe UI", 9))
        return label

    def _create_counter(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        label.setObjectName("counterLabel")
        label.setFont(QFont("Segoe UI", 9))
        return label

    def _create_line_edit(self, placeholder="", max_length=100) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMaxLength(max_length)
        field.setFixedHeight(48)
        field.setObjectName("lineField")
        field.setFont(QFont("Segoe UI", 11))
        return field

    def _create_text_edit(self, placeholder="", max_height=120) -> QTextEdit:
        field = QTextEdit()
        field.setPlaceholderText(placeholder)
        field.setMaximumHeight(max_height)
        field.setObjectName("textField")
        field.setFont(QFont("Segoe UI", 11))
        return field

    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            #settingsContent {
                background: transparent;
            }
            #sectionCard, #actionBar {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 24px;
            }
            #sectionTitle {
                color: #F4F8FF;
            }
            #sectionDescription {
                color: #8CA2C3;
            }
            #fieldLabel {
                color: #DCE9FF;
                margin-top: 6px;
            }
            #fieldHint, #counterLabel, #saveHelper {
                color: #7F98B9;
            }
            #lineField, #textField {
                background: rgba(8, 14, 27, 0.90);
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 16px;
                color: #F4F8FF;
                padding: 0 16px;
                selection-background-color: rgba(83, 230, 255, 0.35);
            }
            #textField {
                padding: 12px 16px;
            }
            #lineField:focus, #textField:focus {
                border: 1px solid rgba(83, 230, 255, 0.55);
            }
            #styleChip {
                color: #D5E3F8;
                font-size: 13px;
                padding: 8px 14px;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
                background: rgba(8, 14, 27, 0.90);
            }
            #styleChip:checked {
                color: #04101D;
                background: #53E6FF;
                border-color: #53E6FF;
            }
            #styleChip::indicator {
                width: 0;
                height: 0;
            }
            #subtitlesToggle {
                color: #E8F0FF;
                font-size: 13px;
                spacing: 10px;
            }
            #subtitlesToggle::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid rgba(255, 255, 255, 0.14);
                border-radius: 6px;
                background: rgba(8, 14, 27, 0.90);
            }
            #subtitlesToggle::indicator:checked {
                background: #53E6FF;
                border-color: #53E6FF;
            }
            #saveBtn, #saveBtnSuccess {
                min-width: 220px;
                border: none;
                border-radius: 16px;
                padding: 0 24px;
                color: white;
            }
            #saveBtn {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #53E6FF,
                    stop: 1 #4A7DFF
                );
            }
            #saveBtn:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #6BEAFF,
                    stop: 1 #618FFF
                );
            }
            #saveBtnSuccess {
                background: #1FAA63;
            }
            """
        )
