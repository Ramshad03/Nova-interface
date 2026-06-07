# ─────────────────────────────────────────────
# ROBOT SCREEN — Main Nova-style fullscreen UI
# Has settings button that opens dashboard
# Robot pauses when dashboard is open
# ─────────────────────────────────────────────

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton,
                              QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
from ui.components import AriaOrb, SubtitleBar, StatusIndicator
from config.config_manager import config


class RobotScreen(QMainWindow):

    # ─── Signals ──────────────────────────────
    signal_state    = pyqtSignal(str)
    signal_subtitle = pyqtSignal(str, str)
    signal_clear    = pyqtSignal()
    signal_language = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_state = "idle"
        self.dashboard_open = False
        self._setup_window()
        self._setup_ui()
        self._apply_stylesheet()
        self._connect_signals()

    # ─── Window Setup ─────────────────────────
    def _setup_window(self):
        self.setWindowTitle("Robot Assistant")
        self.setMinimumSize(900, 700)

    # ─── Build UI ─────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Stacked Widget ───────────────────
        # Page 0 = Robot Home
        # Page 1 = Dashboard (settings)
        self.stack = QStackedWidget()

        # ─── Page 0: Robot Home ───────────────
        self.home_page = self._build_home_page()
        self.stack.addWidget(self.home_page)

        # ─── Page 1: Dashboard ────────────────
        # Imported here to avoid circular imports
        from dashboard.dashboard_window import DashboardWindow
        self.dashboard_page = DashboardWindow(embedded=True)
        self.dashboard_page.on_close_requested = self._close_dashboard
        self.stack.addWidget(self.dashboard_page)

        main_layout.addWidget(self.stack)

    # ─────────────────────────────────────────
    # HOME PAGE
    # ─────────────────────────────────────────
    def _build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─── Top Bar ──────────────────────────
        layout.addWidget(self._build_top_bar())

        # ─── Center Orb ───────────────────────
        orb_container = QWidget()
        orb_layout = QVBoxLayout(orb_container)
        orb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orb = AriaOrb()
        orb_layout.addWidget(
            self.orb, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(orb_container, stretch=1)

        # ─── Bottom Section ───────────────────
        layout.addWidget(self._build_bottom_section())

        return page

    # ─── Top Bar ──────────────────────────────
    def _build_top_bar(self):
        top = QWidget()
        top.setFixedHeight(80)
        top.setObjectName("topBar")
        layout = QHBoxLayout(top)
        layout.setContentsMargins(30, 0, 30, 0)

        # ─── Robot name (dynamic from config) ─
        self.name_label = QLabel(f"✦ {config.robot_name.upper()}")
        self.name_label.setObjectName("robotName")
        self.name_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))

        # ─── Status ───────────────────────────
        self.status = StatusIndicator()

        # ─── Right side ───────────────────────
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Language indicator
        self.lang_label = QLabel("EN")
        self.lang_label.setObjectName("langLabel")
        self.lang_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        # Settings Button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(44, 44)
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFont(QFont("Arial", 20))
        self.settings_btn.setToolTip("Open Settings")
        self.settings_btn.clicked.connect(self._open_dashboard)

        right_layout.addWidget(self.lang_label)
        right_layout.addWidget(self.settings_btn)

        # ─── Add to layout ────────────────────
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addWidget(right_widget)

        return top

    # ─── Bottom Section ───────────────────────
    def _build_bottom_section(self):
        bottom = QWidget()
        bottom.setFixedHeight(160)
        bottom.setObjectName("bottomSection")
        layout = QVBoxLayout(bottom)
        layout.setContentsMargins(0, 0, 0, 20)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(0, 212, 255, 0.2);")

        self.subtitle_bar = SubtitleBar()

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setObjectName("hintLabel")

        layout.addWidget(divider)
        layout.addWidget(self.subtitle_bar)
        layout.addWidget(self.hint_label)

        return bottom

    # ─────────────────────────────────────────
    # DASHBOARD OPEN / CLOSE
    # ─────────────────────────────────────────
    def _open_dashboard(self):
        """Open dashboard — pause robot."""
        self.dashboard_open = True
        self.stack.setCurrentIndex(1)
        try:
            from core.interaction_loop import interaction_loop
            interaction_loop.pause()
            print("[UI] Dashboard opened — robot paused ⏸")
        except Exception as e:
            print(f"[UI] Pause error: {e}")

    def _close_dashboard(self):
        """Close dashboard — resume robot."""
        self.dashboard_open = False
        self.stack.setCurrentIndex(0)

        # ─── Refresh name from latest config ──
        self.refresh_robot_name()

        try:
            from core.interaction_loop import interaction_loop
            interaction_loop.resume()
            print("[UI] Dashboard closed — robot resumed ▶")
        except Exception as e:
            print(f"[UI] Resume error: {e}")

    # ─── Refresh robot name from config ───────
    def refresh_robot_name(self):
        """Update displayed name after dashboard save."""
        from config.config_manager import ConfigManager
        fresh = ConfigManager()
        self.name_label.setText(f"✦ {fresh.robot_name.upper()}")

    # ─────────────────────────────────────────
    # SIGNALS & SLOTS
    # ─────────────────────────────────────────
    def _connect_signals(self):
        self.signal_state.connect(self._slot_set_state)
        self.signal_subtitle.connect(self._slot_show_subtitle)
        self.signal_clear.connect(self._slot_clear_subtitle)
        self.signal_language.connect(self._slot_set_language)

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

    @pyqtSlot(str)
    def _slot_set_state(self, state: str):
        self.current_state = state
        self.orb.set_state(state)
        self.status.set_status(state)
        self.hint_label.setVisible(state == "idle")

    @pyqtSlot(str, str)
    def _slot_show_subtitle(self, text: str, speaker: str):
        self.subtitle_bar.set_text(text, speaker)

    @pyqtSlot()
    def _slot_clear_subtitle(self):
        self.subtitle_bar.clear()

    @pyqtSlot(str)
    def _slot_set_language(self, lang: str):
        self.lang_label.setText(lang.upper())
        color = "#FF6B9D" if lang == "ar" else "#7B2FBE"
        self.lang_label.setStyleSheet(f"""
            color: {color};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 3px;
            padding: 4px 12px;
            border: 1px solid {color};
            border-radius: 4px;
        """)

    # ─── Stylesheet ───────────────────────────
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0A0A1A;
            }
            #topBar {
                background: rgba(0,0,0,0.3);
                border-bottom: 1px solid rgba(0,212,255,0.15);
            }
            #robotName {
                color: #00D4FF;
                letter-spacing: 8px;
            }
            #langLabel {
                color: #7B2FBE;
                letter-spacing: 3px;
                padding: 4px 12px;
                border: 1px solid #7B2FBE;
                border-radius: 4px;
            }
            #settingsBtn {
                background: transparent;
                color: #444466;
                border: 1px solid #333355;
                border-radius: 22px;
            }
            #settingsBtn:hover {
                color: #00D4FF;
                border: 1px solid #00D4FF;
                background: rgba(0,212,255,0.08);
            }
            #bottomSection {
                background: rgba(0,0,0,0.4);
            }
            #hintLabel {
                color: #333355;
                font-size: 13px;
                letter-spacing: 2px;
            }
        """)