from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QWidget

from app.config import FOCUS_POLL_INTERVAL_MS
from app.services.windows_api import (
    WindowHandle,
    get_foreground_window,
    is_window,
    restore_window,
)


class FocusTracker(QObject):
    """Yazmanin hangi pencereye gidecegini takip eder. Yazma sirasinda on pencere
    degisirse metin yanlis uygulamaya sacilir; typing_thread'den cagrilan
    is_target_focused() bunu yakalar."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._own_window_handles: set[WindowHandle] = set()
        self._last_external_window: WindowHandle | None = None
        self._typing_target: WindowHandle | None = None

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

    def lock_target(self) -> WindowHandle | None:
        """Yazma baslarken hedefi sabitler: o an ondeki pencere (kendimiz degilsek),
        degilse en son gorulen dis pencere."""
        current_window = get_foreground_window()
        if current_window and current_window not in self._own_window_handles:
            self._typing_target = current_window
        else:
            self._typing_target = self._last_external_window

        return self._typing_target

    def release_target(self) -> None:
        self._typing_target = None

    def is_target_focused(self) -> bool:
        if self._typing_target is None:
            return True

        return get_foreground_window() == self._typing_target

    def restore_last_window(self) -> bool:
        if not self._last_external_window or not is_window(self._last_external_window):
            return False

        return restore_window(self._last_external_window)
