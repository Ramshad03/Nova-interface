# ─────────────────────────────────────────────
# DASHBOARD WINDOW — Embedded inside Robot Screen
# Opens when settings button pressed
# Has back button to return to robot home
# ─────────────────────────────────────────────

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dashboard.settings_panel import SettingsPanel
from config.config_manager import config


class DashboardWindow(QWidget):

    def __init__(self, embedded=False, parent=None):
        super().__init__(parent)
        self.embedded = embedded
        self.on_close_requested = None
        self._setup_ui()
        self._apply_stylesheet()

    # ─── Build UI ─────────────────────────────
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Header ───────────────────────────
        main_layout.addWidget(self._build_header())

        # ─── Content ──────────────────────────
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        content_layout.addWidget(self._build_sidebar())

        # ─── Stack ────────────────────────────
        self.stack = QStackedWidget()

        # Page 0 — Empty welcome page
        self.welcome_page = self._build_welcome_page()
        self.stack.addWidget(self.welcome_page)

        # Page 1 — Basic Information
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_saved.connect(self._on_settings_saved)
        self.stack.addWidget(self.settings_panel)

        # Start on welcome page
        self.stack.setCurrentIndex(0)
        content_layout.addWidget(self.stack, stretch=1)

        main_layout.addWidget(content, stretch=1)

    # ─── Header ───────────────────────────────
    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(70)
        header.setObjectName("dashHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 30, 0)
        layout.setSpacing(15)

        # ─── Back Button ──────────────────────
        self.back_btn = QPushButton("← Back to Robot")
        self.back_btn.setFixedHeight(38)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setFont(QFont("Arial", 12))
        self.back_btn.clicked.connect(self._on_back_clicked)

        # Title
        title = QLabel("⚙  ALEXA DASHBOARD")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(
            "color: #00D4FF; letter-spacing: 4px;"
        )

        # Status
        self.status_label = QLabel("● ROBOT PAUSED")
        self.status_label.setStyleSheet(
            "color: #FFB800; font-size: 12px; letter-spacing: 2px;"
        )

        layout.addWidget(self.back_btn)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.status_label)

        return header

    # ─── Sidebar ──────────────────────────────
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)

        # ─── Settings Section Label ───────────
        section_label = QLabel("  SETTINGS")
        section_label.setStyleSheet(
            "color: #333355; font-size: 11px; "
            "letter-spacing: 3px; padding: 10px 0 5px 20px;"
        )
        layout.addWidget(section_label)

        # ─── Basic Information Button ─────────
        self.basic_info_btn = QPushButton("  📋  Basic Information")
        self.basic_info_btn.setFixedHeight(48)
        self.basic_info_btn.setFont(QFont("Arial", 13))
        self.basic_info_btn.setObjectName("navBtnActive")
        self.basic_info_btn.clicked.connect(
            lambda: self._show_page(0, self.basic_info_btn)
        )
        layout.addWidget(self.basic_info_btn)

        # ─── Conversation Button ──────────────
        self.conversation_btn = QPushButton("  💬  Conversation")
        self.conversation_btn.setFixedHeight(48)
        self.conversation_btn.setFont(QFont("Arial", 13))
        self.conversation_btn.setObjectName("navBtn")
        self.conversation_btn.clicked.connect(
            lambda: self._show_page(0, self.conversation_btn)
        )
        layout.addWidget(self.conversation_btn)

        # ─── UI Settings Button ───────────────
        self.ui_settings_btn = QPushButton("  🎨  UI Settings")
        self.ui_settings_btn.setFixedHeight(48)
        self.ui_settings_btn.setFont(QFont("Arial", 13))
        self.ui_settings_btn.setObjectName("navBtn")
        self.ui_settings_btn.clicked.connect(
            lambda: self._show_page(0, self.ui_settings_btn)
        )
        layout.addWidget(self.ui_settings_btn)

        # ─── Store nav buttons for highlight ──
        self.nav_btn_list = [
            self.basic_info_btn,
            self.conversation_btn,
            self.ui_settings_btn,
        ]

        layout.addStretch()

        version = QLabel("ALEXA v1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(
            "color: #333355; font-size: 11px; letter-spacing: 2px;"
        )
        layout.addWidget(version)

        return sidebar

    # ─── Welcome Page ────────────────────────
    def _build_welcome_page(self):
        """Empty page shown when no nav item selected."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⚙")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 60px; color: #1A1A3A;")

        hint = QLabel("Select a section from the left to configure")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            "color: #333355; font-size: 16px; letter-spacing: 1px;"
        )

        layout.addWidget(icon)
        layout.addWidget(hint)
        return page

    # ─── Show Page + Highlight Active Button ──
    def _show_page(self, page_index: int, clicked_btn: QPushButton):
        """Show correct page and highlight active nav button."""

        # Map button to correct stack page
        page_map = {
            self.basic_info_btn:    1,   # Settings panel
            self.conversation_btn:  0,   # Welcome (coming soon)
            self.ui_settings_btn:   0,   # Welcome (coming soon)
        }
        self.stack.setCurrentIndex(page_map[clicked_btn])

        # ─── Highlight active button ──────────
        for btn in self.nav_btn_list:
            if btn == clicked_btn:
                btn.setObjectName("navBtnActive")
            else:
                btn.setObjectName("navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ─── Back Button Clicked ──────────────────
    def _on_back_clicked(self):
        """Return to robot home screen."""
        if self.on_close_requested:
            self.on_close_requested()

    # ─── Settings Saved ───────────────────────
    def _on_settings_saved(self):
        self.status_label.setText("● CONFIG UPDATED")
        self.status_label.setStyleSheet(
            "color: #00FF88; font-size: 12px; letter-spacing: 2px;"
        )
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self._reset_status)

    def _reset_status(self):
        self.status_label.setText("● ROBOT PAUSED")
        self.status_label.setStyleSheet(
            "color: #FFB800; font-size: 12px; letter-spacing: 2px;"
        )

    # ─── Stylesheet ───────────────────────────
    def _apply_stylesheet(self):
        self.setStyleSheet(
            "QWidget { background-color: #0F0F1F; color: #FFFFFF; }"
            "#dashHeader { background: #0A0A15; }"
            "#backBtn {"
            "  background: transparent;"
            "  color: #00D4FF;"
            "  border: 1px solid #00D4FF;"
            "  border-radius: 8px;"
            "  padding: 0 15px;"
            "}"
            "#backBtn:hover { background: #112233; }"
            "#sidebar { background: #0A0A15; }"
            "#navBtn {"
            "  background: transparent;"
            "  color: #666688;"
            "  border: none;"
            "  text-align: left;"
            "  padding-left: 20px;"
            "  border-radius: 0px;"
            "}"
            "#navBtn:hover { background: #111133; color: #00D4FF; }"
            "#navBtnActive {"
            "  background: #111133;"
            "  color: #00D4FF;"
            "  padding-left: 17px;"
            "  border: none;"
            "  text-align: left;"
            "  border-radius: 0px;"
            "}"
        )