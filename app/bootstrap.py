from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.application import TrayApplication
from app.config import APP_NAME
from app.resources import build_app_icon
from app.styles import APP_STYLESHEET


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app.setWindowIcon(build_app_icon())

    tray_application = TrayApplication(app)
    tray_application.start()

    return app.exec()
