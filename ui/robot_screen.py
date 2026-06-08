from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.config_manager import config
from ui.components import AriaOrb, StatusIndicator, SubtitleBar


class RobotScreen(QMainWindow):
    signal_state = pyqtSignal(str)
    signal_subtitle = pyqtSignal(str, str)
    signal_clear = pyqtSignal()
    signal_language = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_state = "idle"
        self.current_lang = "en"
        self.dashboard_open = False
        self._stack_animation = None
        self._setup_window()
        self._setup_ui()
        self._apply_stylesheet()
        self._connect_signals()
        self._apply_language_button_style()
        self._update_idle_copy("idle")

    def _setup_window(self):
        self.setWindowTitle("Robot Assistant")
        self.setMinimumSize(900, 700)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("robotRoot")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        self.stack = QStackedWidget()
        self.stack.setObjectName("screenStack")

        self.home_page = self._build_home_page()
        self.stack.addWidget(self.home_page)

        from dashboard.dashboard_window import DashboardWindow

        self.dashboard_page = DashboardWindow(embedded=True)
        self.dashboard_page.on_close_requested = self._close_dashboard
        self.dashboard_page.ui_settings_changed.connect(self._apply_ui_settings)
        self.stack.addWidget(self.dashboard_page)

        main_layout.addWidget(self.stack)

    def _build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(self._build_top_bar())

        center_shell = QWidget()
        center_shell.setObjectName("centerShell")
        center_layout = QVBoxLayout(center_shell)
        center_layout.setContentsMargins(28, 12, 28, 12)
        center_layout.setSpacing(18)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hero_label = QLabel("Ready when someone walks up.")
        self.hero_label.setObjectName("heroLabel")
        self.hero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hero_label.setWordWrap(True)
        self.hero_label.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))

        self.secondary_label = QLabel("")
        self.secondary_label.setObjectName("secondaryLabel")
        self.secondary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_label.setWordWrap(True)
        self.secondary_label.setFont(QFont("Segoe UI", 11))

        self.orb = AriaOrb()

        center_layout.addWidget(self.hero_label)
        center_layout.addWidget(self.secondary_label)
        center_layout.addWidget(
            self.orb,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(center_shell, stretch=1)
        layout.addWidget(self._build_bottom_section())
        return page

    def _build_top_bar(self):
        top = QWidget()
        top.setFixedHeight(94)
        top.setObjectName("topBar")
        layout = QHBoxLayout(top)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(18)

        identity_panel = QWidget()
        identity_panel.setObjectName("identityPanel")
        identity_layout = QVBoxLayout(identity_panel)
        identity_layout.setContentsMargins(18, 14, 18, 14)
        identity_layout.setSpacing(4)

        self.name_label = QLabel(config.robot_name.upper())
        self.name_label.setObjectName("robotName")
        self.name_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))

        self.identity_hint = QLabel("")
        self.identity_hint.setObjectName("identityHint")
        self.identity_hint.setFont(QFont("Segoe UI", 9))

        identity_layout.addWidget(self.name_label)
        identity_layout.addWidget(self.identity_hint)

        self.status = StatusIndicator()

        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self.lang_btn = QPushButton("EN")
        self.lang_btn.setObjectName("langBtn")
        self.lang_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lang_btn.setFixedSize(72, 46)
        self.lang_btn.setToolTip("Click to switch language")
        self.lang_btn.clicked.connect(self._toggle_language)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedHeight(46)
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.settings_btn.setToolTip("Open Settings")
        self.settings_btn.clicked.connect(self._open_dashboard)

        right_layout.addWidget(self.lang_btn)
        right_layout.addWidget(self.settings_btn)

        layout.addWidget(identity_panel)
        layout.addStretch()
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addWidget(right_widget)
        return top

    def _build_bottom_section(self):
        bottom = QWidget()
        bottom.setObjectName("bottomSection")
        layout = QVBoxLayout(bottom)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setObjectName("bottomDivider")

        self.subtitle_bar = SubtitleBar()

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setWordWrap(True)
        self.hint_label.setFont(QFont("Segoe UI", 10))

        layout.addWidget(divider)
        layout.addWidget(self.subtitle_bar)
        layout.addWidget(self.hint_label)
        return bottom

    def _apply_language_button_style(self):
        if self.current_lang == "ar":
            border = "#FF7AB6"
            fill = "rgba(255, 122, 182, 0.12)"
        else:
            border = "#53E6FF"
            fill = "rgba(83, 230, 255, 0.10)"

        self.lang_btn.setStyleSheet(
            f"""
            QPushButton {{
                color: {border};
                border: 1px solid {border};
                border-radius: 16px;
                background: {fill};
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
            }}
            """
        )

    def _toggle_language(self):
        try:
            from core.interaction_loop import interaction_loop

            if self.current_lang == "en":
                self.current_lang = "ar"
                self.lang_btn.setText("AR")
                interaction_loop.forced_language = "ar"
                print("[UI] Language forced to Arabic")
            else:
                self.current_lang = "en"
                self.lang_btn.setText("EN")
                interaction_loop.forced_language = None
                print("[UI] Language set to Auto (English default)")

            self._apply_language_button_style()
        except Exception as error:
            print(f"[UI] Language toggle error: {error}")

    def _switch_stack_page(self, index: int):
        target = self.stack.widget(index)
        if target is None:
            return

        effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self.stack.setCurrentIndex(index)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def cleanup():
            target.setGraphicsEffect(None)

        animation.finished.connect(cleanup)
        animation.start()
        self._stack_animation = animation

    def _open_dashboard(self):
        self.dashboard_open = True
        self._switch_stack_page(1)
        try:
            from core.interaction_loop import interaction_loop

            interaction_loop.pause()
            print("[UI] Dashboard opened - robot paused")
        except Exception as error:
            print(f"[UI] Pause error: {error}")

    def _close_dashboard(self):
        self.dashboard_open = False
        self._switch_stack_page(0)
        self.refresh_robot_name()
        try:
            from core.interaction_loop import interaction_loop

            interaction_loop.resume()
            print("[UI] Dashboard closed - robot resumed")
        except Exception as error:
            print(f"[UI] Resume error: {error}")

    def refresh_robot_name(self):
        from config.config_manager import ConfigManager

        fresh = ConfigManager()
        self.name_label.setText(fresh.robot_name.upper())

    def _connect_signals(self):
        self.signal_state.connect(self._slot_set_state)
        self.signal_subtitle.connect(self._slot_show_subtitle)
        self.signal_clear.connect(self._slot_clear_subtitle)
        self.signal_language.connect(self._slot_set_language)
        # Apply saved UI preferences on startup
        self._apply_ui_settings()

    def _apply_ui_settings(self):
        """Read UI settings from config and apply them live."""
        show_sub = config.get("ui", "show_subtitles", default=True)
        self.subtitle_bar.setVisible(show_sub)

        speed = config.get("ui", "animation_speed", default=1.0)
        self.orb.set_speed(float(speed))

    def set_state(self, state: str):
        if not self.dashboard_open:
            self.signal_state.emit(state)

    def show_subtitle(self, text: str, speaker: str = "ALEXA"):
        if not self.dashboard_open:
            self.signal_subtitle.emit(text, speaker)

    def clear_subtitle(self):
        self.signal_clear.emit()

    def set_language(self, lang: str):
        self.signal_language.emit(lang)

    def _update_idle_copy(self, state: str):
        copy_map = {
            "idle": (
                "Ready when someone walks up.",
                "",
                "",
            ),
            "listening": (
                "Listening carefully.",
                "",
                "",
            ),
            "capturing": (
                "Go ahead, I'm hearing you.",
                "",
                "",
            ),
            "thinking": (
                "Working on a response.",
                "",
                "",
            ),
            "speaking": (
                "Responding out loud.",
                "",
                "",
            ),
        }
        hero, sub, hint = copy_map.get(state, copy_map["idle"])
        self.hero_label.setText(hero)
        self.secondary_label.setText(sub)
        self.hint_label.setText(hint)

    @pyqtSlot(str)
    def _slot_set_state(self, state: str):
        self.current_state = state
        self.orb.set_state(state)
        self.status.set_status(state)
        self._update_idle_copy(state)
        if state == "thinking":
            self.subtitle_bar.clear_robot_text()

    @pyqtSlot(str, str)
    def _slot_show_subtitle(self, text: str, speaker: str):
        self.subtitle_bar.set_text(text, speaker)

    @pyqtSlot()
    def _slot_clear_subtitle(self):
        self.subtitle_bar.clear()

    @pyqtSlot(str)
    def _slot_set_language(self, lang: str):
        del lang
        if not self.dashboard_open:
            pass

    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #040913;
                color: #F4F8FF;
            }
            #robotRoot {
                background: qradialgradient(
                    cx: 0.5, cy: 0.4, radius: 1.1,
                    fx: 0.5, fy: 0.35,
                    stop: 0 rgba(24, 56, 100, 0.42),
                    stop: 0.45 rgba(8, 15, 28, 0.94),
                    stop: 1 #030711
                );
            }
            #screenStack {
                background: transparent;
            }
            #topBar, #centerShell, #bottomSection, #identityPanel {
                border-radius: 28px;
            }
            #topBar {
                background: rgba(8, 14, 27, 0.86);
                border: 1px solid rgba(255, 255, 255, 0.07);
            }
            #identityPanel {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
            #robotName {
                color: #53E6FF;
                letter-spacing: 4px;
            }
            #identityHint {
                color: #8BA6C9;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            #heroLabel {
                color: #F5FAFF;
            }
            #secondaryLabel {
                color: #8CA2C3;
                max-width: 720px;
            }
            #centerShell {
                background: rgba(6, 12, 24, 0.70);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            #settingsBtn {
                background: rgba(255, 255, 255, 0.03);
                color: #E8F0FF;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
                padding: 0 18px;
            }
            #settingsBtn:hover {
                background: rgba(83, 230, 255, 0.12);
                border-color: rgba(83, 230, 255, 0.35);
            }
            #bottomSection {
                background: rgba(8, 14, 27, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.06);
                padding: 18px 22px 20px 22px;
            }
            #bottomDivider {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(83, 230, 255, 0),
                    stop: 0.5 rgba(83, 230, 255, 0.34),
                    stop: 1 rgba(83, 230, 255, 0)
                );
            }
            #hintLabel {
                color: #7F98B9;
                letter-spacing: 1px;
            }
            """
        )
