# powered by mucahid erdogan
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.application import WindowApplication
from app.config import APP_NAME
from app.resources import build_app_icon
from app.styles import APP_STYLESHEET


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app.setWindowIcon(build_app_icon())

    window_application = WindowApplication(app)
    window_application.start()

    return app.exec()

