import math
from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


STATE_THEMES = {
    "idle": {
        "primary": "#53E6FF",
        "accent": "#2687FF",
        "dark": "#07111F",
        "glow": "#7AF2FF",
        "intensity": 0.55,
    },
    "listening": {
        "primary": "#5CF5A1",
        "accent": "#0ABF7A",
        "dark": "#071A14",
        "glow": "#A4FFD0",
        "intensity": 0.8,
    },
    "capturing": {
        "primary": "#FFE033",
        "accent": "#FF9900",
        "dark": "#181000",
        "glow": "#FFF5AA",
        "intensity": 0.88,
    },
    "thinking": {
        "primary": "#FFC857",
        "accent": "#FF8A3D",
        "dark": "#1B1205",
        "glow": "#FFE29D",
        "intensity": 0.72,
    },
    "speaking": {
        "primary": "#FF7AB6",
        "accent": "#9C5BFF",
        "dark": "#180813",
        "glow": "#FFC2DD",
        "intensity": 0.92,
    },
}


class AriaOrb(QWidget):
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_CAPTURING = "capturing"
    STATE_THINKING = "thinking"
    STATE_SPEAKING = "speaking"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = self.STATE_IDLE
        self.animation_step = 0.0
        self.wave_offset = 0.0
        self.pulse_radius = 0.0
        self.state_intensity = STATE_THEMES[self.STATE_IDLE]["intensity"]
        self.target_intensity = self.state_intensity
        self._speed_factor = 1.0
        self.setMinimumSize(420, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(24)

    def set_speed(self, factor: float) -> None:
        self._speed_factor = max(0.3, min(3.0, float(factor)))
        self.timer.setInterval(max(8, int(24 / self._speed_factor)))

    def set_state(self, state: str):
        self.state = state
        self.target_intensity = STATE_THEMES.get(
            state, STATE_THEMES[self.STATE_IDLE]
        )["intensity"]
        self.update()

    def _animate(self):
        self.animation_step += 0.05 * self._speed_factor
        self.wave_offset += 0.08 * self._speed_factor
        self.state_intensity += (
            self.target_intensity - self.state_intensity
        ) * 0.08
        self.pulse_radius = math.sin(self.animation_step * 1.8) * (
            10 + (18 * self.state_intensity)
        )
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        cx = width / 2
        cy = height / 2
        base_radius = min(width, height) * 0.24

        theme = STATE_THEMES.get(self.state, STATE_THEMES[self.STATE_IDLE])
        primary = QColor(theme["primary"])
        accent = QColor(theme["accent"])
        dark = QColor(theme["dark"])
        glow = QColor(theme["glow"])

        self._draw_ambient_field(
            painter, cx, cy, base_radius, primary, accent, glow
        )
        self._draw_outer_rings(
            painter, cx, cy, base_radius, primary, glow
        )
        self._draw_orb_body(
            painter, cx, cy, base_radius, primary, accent, dark, glow
        )

        if self.state == self.STATE_SPEAKING:
            self._draw_sound_waves(painter, cx, cy, base_radius, primary)
        elif self.state == self.STATE_CAPTURING:
            self._draw_capturing_bars(painter, cx, cy, base_radius, primary, glow)
        elif self.state == self.STATE_LISTENING:
            self._draw_listening_dots(
                painter, cx, cy, base_radius, primary
            )
        elif self.state == self.STATE_THINKING:
            self._draw_thinking_arc(
                painter, cx, cy, base_radius, glow, accent
            )

        painter.end()

    def _draw_ambient_field(self, painter, cx, cy, radius, primary, accent, glow):
        field_gradient = QRadialGradient(cx, cy, radius * 2.1)
        outer = QColor("#020611")
        field_gradient.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), 28))
        field_gradient.setColorAt(0.45, QColor(primary.red(), primary.green(), primary.blue(), 16))
        field_gradient.setColorAt(1.0, outer)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(field_gradient))
        painter.drawEllipse(
            QPointF(cx, cy), radius * 2.1, radius * 2.1
        )

        ring_gradient = QConicalGradient(QPointF(cx, cy), self.animation_step * 90)
        ring_gradient.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 100))
        ring_gradient.setColorAt(0.35, QColor(primary.red(), primary.green(), primary.blue(), 18))
        ring_gradient.setColorAt(0.7, QColor(glow.red(), glow.green(), glow.blue(), 120))
        ring_gradient.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 100))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QBrush(ring_gradient), 1.5))
        painter.drawEllipse(QPointF(cx, cy), radius * 1.45, radius * 1.45)

    def _draw_outer_rings(self, painter, cx, cy, radius, primary, glow):
        for index in range(4):
            ring_radius = radius + 32 + (index * 26) + self.pulse_radius
            alpha = max(16, 80 - (index * 18))
            ring_color = QColor(primary.red(), primary.green(), primary.blue(), alpha)
            painter.setPen(QPen(ring_color, 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_radius, ring_radius)

        soft_glow = QRadialGradient(cx, cy, radius + 72)
        soft_glow.setColorAt(
            0.0,
            QColor(glow.red(), glow.green(), glow.blue(), 60),
        )
        soft_glow.setColorAt(
            0.55,
            QColor(primary.red(), primary.green(), primary.blue(), 16),
        )
        soft_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(soft_glow))
        painter.drawEllipse(QPointF(cx, cy), radius + 72, radius + 72)

    def _draw_orb_body(self, painter, cx, cy, radius, primary, accent, dark, glow):
        orb_gradient = QRadialGradient(
            cx - (radius * 0.28),
            cy - (radius * 0.34),
            radius * 1.25,
        )
        orb_gradient.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), 230))
        orb_gradient.setColorAt(0.28, QColor(primary.red(), primary.green(), primary.blue(), 255))
        orb_gradient.setColorAt(0.72, QColor(accent.red(), accent.green(), accent.blue(), 245))
        orb_gradient.setColorAt(1.0, dark)
        painter.setBrush(QBrush(orb_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        core_gradient = QRadialGradient(
            cx - (radius * 0.14),
            cy - (radius * 0.18),
            radius * 0.92,
        )
        core_gradient.setColorAt(0.0, QColor(255, 255, 255, 180))
        core_gradient.setColorAt(0.25, QColor(glow.red(), glow.green(), glow.blue(), 120))
        core_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.74, radius * 0.74)

        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius * 0.92, radius * 0.92)

    def _draw_sound_waves(self, painter, cx, cy, radius, color):
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(1, 5):
            wave_radius = radius + 20 + (index * 24)
            alpha = int(170 * math.sin(self.wave_offset - index * 0.45) ** 2)
            wave_color = QColor(color.red(), color.green(), color.blue(), max(18, alpha))
            painter.setPen(QPen(wave_color, 2))
            painter.drawEllipse(QPointF(cx, cy), wave_radius, wave_radius * 0.34)

    def _draw_capturing_bars(self, painter, cx, cy, radius, color, glow):
        """Animated equalizer bars — shows the mic is actively capturing speech."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        bar_count = 7
        bar_width = 6
        gap = 11
        total_width = bar_count * bar_width + (bar_count - 1) * gap
        start_x = cx - total_width / 2
        base_y = cy + radius + 48
        max_height = 36

        for i in range(bar_count):
            phase = self.wave_offset * 2.8 + i * 0.85
            height = max(6, max_height * (0.45 + 0.55 * (math.sin(phase) + 1) / 2))
            alpha = int(160 + 80 * (math.sin(phase + 0.4) + 1) / 2)
            bar_color = QColor(color.red(), color.green(), color.blue(), alpha)
            x = start_x + i * (bar_width + gap)
            painter.setBrush(QBrush(bar_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                int(x), int(base_y - height), bar_width, int(height), 3, 3
            )

        # Subtle label glow ring
        glow_color = QColor(glow.red(), glow.green(), glow.blue(), 40)
        painter.setPen(QPen(glow_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius + 22, radius + 22)

    def _draw_listening_dots(self, painter, cx, cy, radius, color):
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(10):
            angle = (index / 10) * math.tau + self.wave_offset
            distance = radius + 38 + (math.sin(self.wave_offset + index) * 4)
            dot_x = cx + distance * math.cos(angle)
            dot_y = cy + distance * math.sin(angle)
            alpha = int(90 + (110 * (math.sin((self.wave_offset * 2.1) + index) + 1) / 2))
            dot_color = QColor(color.red(), color.green(), color.blue(), alpha)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(QPointF(dot_x, dot_y), 5.5, 5.5)

    def _draw_thinking_arc(self, painter, cx, cy, radius, glow, accent):
        arc_color = QColor(glow.red(), glow.green(), glow.blue(), 180)
        accent_color = QColor(accent.red(), accent.green(), accent.blue(), 140)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(arc_color, 3))
        painter.drawArc(
            int(cx - radius * 1.18),
            int(cy - radius * 1.18),
            int(radius * 2.36),
            int(radius * 2.36),
            int(-(self.animation_step * 120) * 16),
            110 * 16,
        )
        painter.setPen(QPen(accent_color, 2))
        painter.drawArc(
            int(cx - radius * 1.34),
            int(cy - radius * 1.34),
            int(radius * 2.68),
            int(radius * 2.68),
            int((self.animation_step * 90) * 16),
            70 * 16,
        )


class SubtitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("subtitleBar")
        self.setMinimumHeight(80)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 16, 28, 16)
        layout.setSpacing(10)

        # User speech row (hidden until user speaks)
        self.user_section = QWidget()
        self.user_section.setObjectName("userSection")
        user_row = QHBoxLayout(self.user_section)
        user_row.setContentsMargins(0, 0, 0, 0)
        user_row.setSpacing(10)

        you_tag = QLabel("YOU")
        you_tag.setObjectName("youTag")
        you_tag.setFont(QFont("Segoe UI Semibold", 9))
        you_tag.setFixedWidth(36)

        self.user_text_label = QLabel("")
        self.user_text_label.setObjectName("userTextLabel")
        self.user_text_label.setWordWrap(True)
        self.user_text_label.setFont(QFont("Segoe UI", 13))
        self.user_text_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        user_row.addWidget(you_tag)
        user_row.addWidget(self.user_text_label, 1)

        # Thin divider between user speech and robot response
        self.separator = QWidget()
        self.separator.setFixedHeight(1)
        self.separator.setObjectName("subtitleSeparator")

        # Robot response rows
        self.speaker_label = QLabel("")
        self.speaker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speaker_label.setObjectName("speakerLabel")
        self.speaker_label.setFont(QFont("Segoe UI Semibold", 10))

        self.subtitle_label = QLabel("")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setFont(QFont("Segoe UI", 15, QFont.Weight.Medium))

        layout.addWidget(self.user_section)
        layout.addWidget(self.separator)
        layout.addWidget(self.speaker_label)
        layout.addWidget(self.subtitle_label)

        self.user_section.hide()
        self.separator.hide()

        self._apply_theme("#53E6FF")

    def _apply_theme(self, accent: str):
        self.setStyleSheet(
            f"""
            #subtitleBar {{
                background: rgba(10, 17, 31, 0.86);
                border: 1px solid rgba(83, 230, 255, 0.16);
                border-radius: 26px;
            }}
            #youTag {{
                color: #5CF5A1;
                letter-spacing: 3px;
            }}
            #userTextLabel {{
                color: #A8D5A8;
            }}
            #subtitleSeparator {{
                background: rgba(255, 255, 255, 0.10);
            }}
            #speakerLabel {{
                color: {accent};
                letter-spacing: 4px;
            }}
            #subtitleLabel {{
                color: #F4F8FF;
            }}
            """
        )

    def set_user_text(self, text: str):
        self.user_text_label.setText(text)
        self.user_section.show()

    def set_robot_text(self, text: str, speaker: str = "ARIA"):
        accent = "#53E6FF" if speaker in ["ALEXA", "ARIA"] else "#FFC857"
        self._apply_theme(accent)
        self.speaker_label.setText(speaker)
        self.subtitle_label.setText(text)
        if self.user_section.isVisible():
            self.separator.show()

    def clear_robot_text(self):
        self.speaker_label.setText("")
        self.subtitle_label.setText("")
        self.separator.hide()

    def set_text(self, text: str, speaker: str = "ARIA"):
        if speaker == "YOU":
            self.set_user_text(text)
        else:
            self.set_robot_text(text, speaker)

    def clear(self):
        self.user_text_label.setText("")
        self.user_section.hide()
        self.separator.hide()
        self.speaker_label.setText("")
        self.subtitle_label.setText("")
        self._apply_theme("#53E6FF")


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusIndicator")
        self.setFixedHeight(46)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)

        self.status_label = QLabel("ACTIVE  IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont("Segoe UI Semibold", 9))
        layout.addWidget(self.status_label)
        self.set_status("idle")

    def set_status(self, state: str):
        labels = {
            "idle": ("ACTIVE  IDLE", "#6B728A"),
            "listening": ("ACTIVE  LISTENING", "#5CF5A1"),
            "capturing": ("ACTIVE  CAPTURING", "#FFE033"),
            "thinking": ("ACTIVE  THINKING", "#FFC857"),
            "speaking": ("ACTIVE  SPEAKING", "#FF7AB6"),
        }
        text, color = labels.get(state, labels["idle"])
        self.setStyleSheet(
            f"""
            #statusIndicator {{
                background: rgba(10, 17, 31, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
            }}
            #statusLabel {{
                color: {color};
                letter-spacing: 3px;
            }}
            """
        )
        self.status_label.setText(text)
