from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dashboard.conversation_panel import ConversationPanel
from dashboard.settings_panel import SettingsPanel
from dashboard.ui_settings_panel import UISettingsPanel


class DashboardWindow(QWidget):
    ui_settings_changed = pyqtSignal()   # emitted after UI Settings are saved

    def __init__(self, embedded=False, parent=None):
        super().__init__(parent)
        self.embedded = embedded
        self.on_close_requested = None
        self._page_animation = None
        self._setup_ui()
        self._apply_stylesheet()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        main_layout.addWidget(self._build_header())

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        content_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("dashboardStack")

        self.welcome_page = self._build_welcome_page()
        self.stack.addWidget(self.welcome_page)

        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_saved.connect(self._on_settings_saved)
        self.stack.addWidget(self.settings_panel)

        self.conversation_panel = ConversationPanel()
        self.stack.addWidget(self.conversation_panel)

        self.ui_settings_panel = UISettingsPanel()
        self.ui_settings_panel.settings_saved.connect(self._on_settings_saved)
        self.ui_settings_panel.settings_saved.connect(self.ui_settings_changed)
        self.stack.addWidget(self.ui_settings_panel)

        self.stack.setCurrentIndex(0)
        content_layout.addWidget(self.stack, stretch=1)

        main_layout.addWidget(content, stretch=1)

    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(86)
        header.setObjectName("dashHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        self.back_btn = QPushButton("Back to Robot")
        self.back_btn.setFixedHeight(44)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.back_btn.clicked.connect(self._on_back_clicked)

        title_wrap = QWidget()
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        title = QLabel("Interaction Dashboard")
        title.setObjectName("dashTitle")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))

        subtitle = QLabel("Manage identity, conversation tone, and the live robot interface.")
        subtitle.setObjectName("dashSubtitle")
        subtitle.setFont(QFont("Segoe UI", 10))

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.status_label = QLabel("Robot paused")
        self.status_label.setObjectName("statusPill")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(150)

        layout.addWidget(self.back_btn)
        layout.addWidget(title_wrap)
        layout.addStretch()
        layout.addWidget(self.status_label)
        return header

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 20)
        layout.setSpacing(10)

        section_label = QLabel("SETTINGS")
        section_label.setObjectName("sectionLabel")
        section_label.setFont(QFont("Segoe UI Semibold", 9))
        layout.addWidget(section_label)

        self.basic_info_btn = QPushButton("Basic Information")
        self.basic_info_btn.setFixedHeight(52)
        self.basic_info_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.basic_info_btn.setObjectName("navBtnActive")
        self.basic_info_btn.clicked.connect(
            lambda: self._show_page(0, self.basic_info_btn)
        )
        layout.addWidget(self.basic_info_btn)

        self.conversation_btn = QPushButton("Conversation")
        self.conversation_btn.setFixedHeight(52)
        self.conversation_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.conversation_btn.setObjectName("navBtn")
        self.conversation_btn.clicked.connect(
            lambda: self._show_page(0, self.conversation_btn)
        )
        layout.addWidget(self.conversation_btn)

        self.ui_settings_btn = QPushButton("UI Settings")
        self.ui_settings_btn.setFixedHeight(52)
        self.ui_settings_btn.setFont(QFont("Segoe UI Semibold", 11))
        self.ui_settings_btn.setObjectName("navBtn")
        self.ui_settings_btn.clicked.connect(
            lambda: self._show_page(0, self.ui_settings_btn)
        )
        layout.addWidget(self.ui_settings_btn)

        self.nav_btn_list = [
            self.basic_info_btn,
            self.conversation_btn,
            self.ui_settings_btn,
        ]

        layout.addStretch()

        footer = QLabel("Nova Interaction  1.0.0")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setObjectName("sidebarFooter")
        footer.setFont(QFont("Segoe UI", 9))
        layout.addWidget(footer)
        return sidebar

    def _build_welcome_page(self):
        page = QWidget()
        page.setObjectName("welcomePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(54, 54, 54, 54)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        eyebrow = QLabel("Dashboard overview")
        eyebrow.setObjectName("welcomeEyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Select a section to keep editing the current setup.")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)

        copy = QLabel(
            "All existing controls are still here. This screen is only refined to feel calmer, clearer, and easier to scan."
        )
        copy.setObjectName("welcomeCopy")
        copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy.setWordWrap(True)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(copy)
        return page

    def _animate_current_page(self):
        target = self.stack.currentWidget()
        if target is None:
            return

        effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(180)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def cleanup():
            target.setGraphicsEffect(None)

        animation.finished.connect(cleanup)
        animation.start()
        self._page_animation = animation

    def _show_page(self, page_index: int, clicked_btn: QPushButton):
        page_map = {
            self.basic_info_btn: 1,
            self.conversation_btn: 2,
            self.ui_settings_btn: 3,
        }
        del page_index
        idx = page_map[clicked_btn]
        if idx == 2:
            self.conversation_panel.refresh()
        self.stack.setCurrentIndex(idx)
        self._animate_current_page()

        for btn in self.nav_btn_list:
            btn.setObjectName("navBtnActive" if btn == clicked_btn else "navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_back_clicked(self):
        if self.on_close_requested:
            self.on_close_requested()

    def _on_settings_saved(self):
        self.status_label.setText("Config updated")
        self.status_label.setObjectName("statusPillSuccess")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        QTimer.singleShot(3000, self._reset_status)

    def _reset_status(self):
        self.status_label.setText("Robot paused")
        self.status_label.setObjectName("statusPill")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #050B15;
                color: #F4F8FF;
            }
            #dashHeader, #sidebar, #dashboardStack, #welcomePage {
                border-radius: 28px;
            }
            #dashHeader {
                background: rgba(8, 14, 27, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
            #backBtn {
                background: rgba(255, 255, 255, 0.03);
                color: #53E6FF;
                border: 1px solid rgba(83, 230, 255, 0.28);
                border-radius: 14px;
                padding: 0 18px;
            }
            #backBtn:hover {
                background: rgba(83, 230, 255, 0.11);
            }
            #dashTitle {
                color: #F4F8FF;
            }
            #dashSubtitle {
                color: #8CA2C3;
            }
            #statusPill, #statusPillSuccess {
                padding: 10px 18px;
                border-radius: 16px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            #statusPill {
                color: #FFC857;
                background: rgba(255, 200, 87, 0.10);
                border: 1px solid rgba(255, 200, 87, 0.25);
            }
            #statusPillSuccess {
                color: #5CF5A1;
                background: rgba(92, 245, 161, 0.10);
                border: 1px solid rgba(92, 245, 161, 0.25);
            }
            #sidebar {
                background: rgba(8, 14, 27, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            #sectionLabel {
                color: #7F98B9;
                letter-spacing: 3px;
            }
            #navBtn, #navBtnActive {
                text-align: left;
                padding: 0 18px;
                border-radius: 18px;
                border: 1px solid transparent;
            }
            #navBtn {
                background: transparent;
                color: #8CA2C3;
            }
            #navBtn:hover {
                background: rgba(255, 255, 255, 0.04);
                color: #F4F8FF;
            }
            #navBtnActive {
                background: rgba(83, 230, 255, 0.12);
                color: #53E6FF;
                border-color: rgba(83, 230, 255, 0.28);
            }
            #sidebarFooter {
                color: #7084A4;
                letter-spacing: 2px;
            }
            #dashboardStack {
                background: rgba(8, 14, 27, 0.68);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            #welcomePage {
                background: transparent;
            }
            #welcomeEyebrow {
                color: #53E6FF;
                letter-spacing: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            #welcomeTitle {
                color: #F4F8FF;
                font-size: 28px;
                font-weight: 700;
            }
            #welcomeCopy {
                color: #8CA2C3;
                font-size: 14px;
            }
            """
        )
