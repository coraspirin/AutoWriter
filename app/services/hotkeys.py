# powered by mucahid erdogan
from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

from app.services.windows_api import (
    WM_HOTKEY,
    WindowHandle,
    register_hotkey,
    unregister_hotkey,
)

WINDOWS_EVENT_TYPE = b"windows_generic_MSG"


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


class GlobalHotkeys(QObject, QAbstractNativeEventFilter):
    """Uygulama odakta olmasa da calisan kisayollar (RegisterHotKey).

    Duraklat/Durdur'a fare ile basmak icin uygulama penceresine tiklamak
    gerekir; o an on pencere degisir ve kalan karakterler hedef yerine kendi
    metin kutumuza yazilir. Kisayol bu yuzden zorunlu.
    """

    triggered = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        QAbstractNativeEventFilter.__init__(self)
        self._window_handle: WindowHandle | None = None
        self._registered_ids: list[int] = []

    def register(self, window_handle: WindowHandle, bindings: dict[int, int]) -> list[int]:
        """bindings: {hotkey_id: virtual_key}. Kaydedilemeyen kisayollarin
        id'lerini doner (baska bir uygulama kapmis olabilir)."""
        self._window_handle = window_handle
        failed: list[int] = []

        for hotkey_id, virtual_key in bindings.items():
            if register_hotkey(window_handle, hotkey_id, virtual_key):
                self._registered_ids.append(hotkey_id)
            else:
                failed.append(hotkey_id)

        return failed

    def unregister_all(self) -> None:
        if self._window_handle is None:
            return

        for hotkey_id in self._registered_ids:
            unregister_hotkey(self._window_handle, hotkey_id)

        self._registered_ids.clear()

    def nativeEventFilter(
        self,
        event_type: bytes,
        message: int,
    ) -> tuple[bool, int]:
        if event_type != WINDOWS_EVENT_TYPE:
            return False, 0

        msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents
        if msg.message == WM_HOTKEY and msg.wParam in self._registered_ids:
            self.triggered.emit(int(msg.wParam))

        return False, 0


def make_handler(callback: Callable[[], None]) -> Callable[[int], None]:
    return lambda _hotkey_id: callback()
