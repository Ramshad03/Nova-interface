# ─────────────────────────────────────────────
# UI COMPONENTS — Reusable animated widgets
# Orb animation, subtitle bar, status indicator
# ─────────────────────────────────────────────

import math
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import (QPainter, QColor, QRadialGradient,
                          QLinearGradient, QFont, QPen, QBrush)


# ─────────────────────────────────────────────
# ARIA ORB — Animated glowing orb (robot face)
# ─────────────────────────────────────────────
class AriaOrb(QWidget):

    # ─── Robot States ─────────────────────────
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_THINKING = "thinking"
    STATE_SPEAKING = "speaking"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = self.STATE_IDLE
        self.animation_step = 0
        self.pulse_radius = 0
        self.wave_offset = 0
        self.setMinimumSize(400, 400)

        # ─── Animation Timer ──────────────────
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)  # ~33fps

    # ─── Set Robot State ──────────────────────
    def set_state(self, state: str):
        self.state = state
        self.update()

    # ─── Animation Loop ───────────────────────
    def _animate(self):
        self.animation_step += 1
        self.pulse_radius = math.sin(self.animation_step * 0.05) * 20
        self.wave_offset += 0.1
        self.update()

    # ─── Paint Orb ────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        base_radius = min(w, h) // 3

        # ─── State Colors ─────────────────────
        colors = {
            self.STATE_IDLE:      ("#00D4FF", "#0A0A1A", "#7B2FBE"),
            self.STATE_LISTENING: ("#00FF88", "#0A1A0F", "#00CC66"),
            self.STATE_THINKING:  ("#FFB800", "#1A1400", "#FF8C00"),
            self.STATE_SPEAKING:  ("#FF6B9D", "#1A0A10", "#CC44FF"),
        }
        primary, dark, accent = colors.get(self.state, colors[self.STATE_IDLE])

        # ─── Outer Pulse Rings ────────────────
        for i in range(3):
            ring_r = base_radius + 40 + (i * 30) + self.pulse_radius
            opacity = max(0, 80 - i * 25)
            color = QColor(primary)
            color.setAlpha(opacity)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # ─── Outer Glow ───────────────────────
        glow_grad = QRadialGradient(cx, cy, base_radius + 60)
        glow_color = QColor(primary)
        glow_color.setAlpha(60)
        glow_grad.setColorAt(0, glow_color)
        glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy),
                            base_radius + 60, base_radius + 60)

        # ─── Main Orb Body ────────────────────
        orb_grad = QRadialGradient(cx - base_radius * 0.3,
                                   cy - base_radius * 0.3,
                                   base_radius * 1.2)
        orb_grad.setColorAt(0.0, QColor(primary).lighter(150))
        orb_grad.setColorAt(0.4, QColor(primary))
        orb_grad.setColorAt(0.8, QColor(accent))
        orb_grad.setColorAt(1.0, QColor(dark))
        painter.setBrush(QBrush(orb_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), base_radius, base_radius)

        # ─── Inner Shine ──────────────────────
        shine_grad = QRadialGradient(cx - base_radius * 0.25,
                                     cy - base_radius * 0.35,
                                     base_radius * 0.5)
        shine_grad.setColorAt(0, QColor(255, 255, 255, 120))
        shine_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(shine_grad))
        painter.drawEllipse(QPointF(cx - base_radius * 0.15,
                                    cy - base_radius * 0.2),
                            base_radius * 0.45, base_radius * 0.35)

        # ─── Wave Lines (speaking state) ──────
        if self.state == self.STATE_SPEAKING:
            self._draw_sound_waves(painter, cx, cy, base_radius, primary)

        # ─── Listening Indicator ──────────────
        if self.state == self.STATE_LISTENING:
            self._draw_listening_dots(painter, cx, cy, base_radius, primary)

        painter.end()

    # ─── Sound Wave Animation ─────────────────
    def _draw_sound_waves(self, painter, cx, cy, r, color):
        pen = QPen(QColor(color), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(1, 5):
            wave_r = r + 20 + i * 25
            alpha = int(150 * math.sin(self.wave_offset - i * 0.5) ** 2)
            c = QColor(color)
            c.setAlpha(max(0, alpha))
            painter.setPen(QPen(c, 2))
            painter.drawEllipse(QPointF(cx, cy), wave_r, wave_r * 0.3)

    # ─── Listening Dots Animation ─────────────
    def _draw_listening_dots(self, painter, cx, cy, r, color):
        for i in range(8):
            angle = (i / 8) * 2 * math.pi + self.wave_offset
            dot_x = cx + (r + 40) * math.cos(angle)
            dot_y = cy + (r + 40) * math.sin(angle)
            alpha = int(200 * (math.sin(self.wave_offset * 2 + i) + 1) / 2)
            c = QColor(color)
            c.setAlpha(alpha)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(dot_x, dot_y), 6, 6)


# ─────────────────────────────────────────────
# SUBTITLE BAR — Shows live interaction text
# ─────────────────────────────────────────────
class SubtitleBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self._setup_ui()

    # ─── Setup UI ─────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 10, 40, 10)

        # Speaker label (USER / ARIA)
        self.speaker_label = QLabel("")
        self.speaker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speaker_label.setStyleSheet("""
            color: #00D4FF;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
            text-transform: uppercase;
        """)

        # Subtitle text
        self.subtitle_label = QLabel("")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 400;
            line-height: 1.4;
        """)

        layout.addWidget(self.speaker_label)
        layout.addWidget(self.subtitle_label)

    # ─── Update Subtitle ──────────────────────
    def set_text(self, text: str, speaker: str = "ARIA"):
        color = "#00D4FF" if speaker == "ARIA" else "#00FF88"
        self.speaker_label.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        self.speaker_label.setText(speaker)
        self.subtitle_label.setText(text)

    # ─── Clear Subtitle ───────────────────────
    def clear(self):
        self.speaker_label.setText("")
        self.subtitle_label.setText("")


# ─────────────────────────────────────────────
# STATUS INDICATOR — Top status bar
# ─────────────────────────────────────────────
class StatusIndicator(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)

        self.status_label = QLabel("● IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #555577;
            font-size: 12px;
            letter-spacing: 4px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_label)

    # ─── Update Status ────────────────────────
    def set_status(self, state: str):
        labels = {
            "idle":      ("● IDLE",      "#555577"),
            "listening": ("● LISTENING", "#00FF88"),
            "thinking":  ("● THINKING",  "#FFB800"),
            "speaking":  ("● SPEAKING",  "#FF6B9D"),
        }
        text, color = labels.get(state, ("● IDLE", "#555577"))
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            letter-spacing: 4px;
            font-weight: bold;
        """)
        self.status_label.setText(text)