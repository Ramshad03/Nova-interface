# ─────────────────────────────────────────────
# ARIA ROBOT — MAIN ENTRY POINT
# Launches Robot UI + Dashboard + Voice Loop
# ─────────────────────────────────────────────

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.robot_screen import RobotScreen
from dashboard.dashboard_window import DashboardWindow


# ─── Safe Config Load ─────────────────────────
def load_config():
    try:
        from config.config_manager import config
        return config
    except FileNotFoundError as e:
        _show_fatal_error("Config File Missing", str(e))
    except ValueError as e:
        _show_fatal_error("Config File Invalid", str(e))
    except Exception as e:
        _show_fatal_error("Startup Error", str(e))
    return None


# ─── Fatal Error Dialog ───────────────────────
def _show_fatal_error(title: str, message: str):
    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.critical(None, f"ARIA — {title}", message)
    sys.exit(1)


# ─── Main Entry Point ─────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # ─── Load Config ──────────────────────────
    config = load_config()
    if not config:
        sys.exit(1)

    app.setApplicationName(f"ARIA — {config.robot_name}")

    # ─── Screen Positioning ───────────────────
    screens = app.screens()
    primary_geo = screens[0].geometry()

    # ─── Launch Robot Screen ──────────────────
    robot_screen = RobotScreen()

    if len(screens) > 1:
        secondary_geo = screens[1].geometry()
        robot_screen.move(secondary_geo.left(), secondary_geo.top())
        robot_screen.showFullScreen()
    else:
        robot_screen.move(0, 0)
        robot_screen.resize(
            primary_geo.width() // 2,
            primary_geo.height()
        )
    robot_screen.show()

    # ─── Connect Interaction Loop to UI ───────
    from core.interaction_loop import interaction_loop

    interaction_loop.on_state_change    = robot_screen.set_state
    interaction_loop.on_subtitle        = robot_screen.show_subtitle
    interaction_loop.on_clear_subtitle  = robot_screen.clear_subtitle
    interaction_loop.on_language_change = robot_screen.set_language

    # ─── Start Voice Loop in Background ───────
    import threading
    from PyQt6.QtCore import QTimer
    def start_loop():
        interaction_loop.start()
    QTimer.singleShot(500, lambda: threading.Thread(
        target=start_loop, daemon=True
    ).start())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()