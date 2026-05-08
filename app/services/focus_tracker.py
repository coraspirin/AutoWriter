from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QWidget

from app.config import FOCUS_POLL_INTERVAL_MS
from app.services.windows_api import WindowHandle, get_foreground_window, is_window, restore_window


class FocusTracker(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._own_window_handles: set[WindowHandle] = set()
        self._last_external_window: WindowHandle | None = None

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(FOCUS_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self.capture_now)
        self._poll_timer.start()

    def register_window(self, window: QWidget) -> None:
        self._own_window_handles.add(int(window.winId()))

    def capture_now(self) -> None:
        current_window = get_foreground_window()
        if not current_window or current_window in self._own_window_handles:
            return

        self._last_external_window = current_window

    def restore_last_window(self) -> bool:
        if not self._last_external_window or not is_window(self._last_external_window):
            return False

        return restore_window(self._last_external_window)
