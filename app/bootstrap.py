# powered by mucahid erdogan
from __future__ import annotations

import sys

from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QApplication

from app.application import WindowApplication
from app.config import APP_NAME, APP_VERSION, WINDOW_TITLE
from app.resources import build_app_icon
from app.services.updater import finish_pending_update
from app.services.windows_api import find_window_by_title, restore_window
from app.styles import APP_STYLESHEET

SINGLE_INSTANCE_KEY = "CoraspirinAutoWriter_singleton"


def run() -> int:
    # Guncellemeden sonra baslatildiysak eski surecin kapanmasini bekle; aksi
    # halde asagidaki tek ornek kontrolu yeni surumu hemen kapatir.
    finish_pending_update(sys.argv)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app.setWindowIcon(build_app_icon())

    # Tek ornek: uygulama zaten calisiyorsa ikincisi acilmaz; onun yerine var olan
    # pencereyi one getirip sessizce cikariz. Paylasilan bellek blogu Windows'ta
    # surec olunce otomatik serbest kalir, kilit takili kalmaz.
    single_instance = QSharedMemory(SINGLE_INSTANCE_KEY)
    if not single_instance.create(1):
        existing = find_window_by_title(WINDOW_TITLE)
        if existing:
            restore_window(existing)
        return 0

    window_application = WindowApplication(app)
    window_application.start()

    return app.exec()
