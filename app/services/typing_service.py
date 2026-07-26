# powered by mucahid erdogan
from __future__ import annotations

import time
from threading import Event
from typing import Callable

from app.config import (
    KEY_HOLD_SECONDS,
    LINE_BREAK_EXTRA_SECONDS,
    TYPE_CPS_DEFAULT,
)
from app.services.exceptions import TypingCancelled
from app.services import windows_api

ProgressCallback = Callable[[int, int], None]
FocusGuard = Callable[[], bool]

MODIFIER_RELEASE_TIMEOUT_SECONDS = 2.0


class TextTypingService:
    def __init__(self, cps: int = TYPE_CPS_DEFAULT) -> None:
        self._cps = cps

    def set_speed(self, cps: int) -> None:
        self._cps = max(1, cps)

    def type_text(
        self,
        text: str,
        cancel_event: Event | None = None,
        progress_callback: ProgressCallback | None = None,
        focus_guard: FocusGuard | None = None,
    ) -> None:
        if not text:
            return

        interval_seconds = 1.0 / max(1, self._cps)
        keyboard_layout = windows_api.get_keyboard_layout()
        dead_keys = windows_api.detect_dead_keys(set(text), keyboard_layout)
        total_characters = len(text)

        with windows_api.TimerResolution():
            self._wait_for_modifier_release(cancel_event)

            for index, character in enumerate(text, start=1):
                self._ensure_runnable(cancel_event, focus_guard)

                extra_delay = self._send_character(character, keyboard_layout, dead_keys)

                if progress_callback is not None:
                    progress_callback(index, total_characters)

                remaining = interval_seconds - KEY_HOLD_SECONDS + extra_delay
                self._wait(remaining, cancel_event)

    def _send_character(
        self,
        character: str,
        keyboard_layout: int,
        dead_keys: set[str],
    ) -> float:
        if character == "\n":
            windows_api.send_scancode_key(windows_api.SC_RETURN, hold_seconds=KEY_HOLD_SECONDS)
            # Kod editorlerinin otomatik girintisini her zaman temizle: metin
            # kutusundaki neyse birebir o yazilsin, merdiven olusmasin.
            self._clear_auto_indent()
            return LINE_BREAK_EXTRA_SECONDS

        if character == "\t":
            windows_api.send_scancode_key(windows_api.SC_TAB, hold_seconds=KEY_HOLD_SECONDS)
            return 0.0

        if windows_api.send_character_as_scancode(character, keyboard_layout, KEY_HOLD_SECONDS):
            # Olu tus (^ ~ ` ´): commit boslugu gonder ki aksan standalone cozulsun
            # ve metindeki gercek bosluk yutulmasin.
            if character in dead_keys:
                windows_api.send_scancode_key(windows_api.SC_SPACE, hold_seconds=KEY_HOLD_SECONDS)
            return 0.0

        # Duzende olmayan nadir karakterler (emoji vb.) icin son care.
        windows_api.send_unicode_character(character, KEY_HOLD_SECONDS)
        return 0.0

    def _clear_auto_indent(self) -> None:
        """Kod editorleri Enter'dan sonra onceki satirin girintisini otomatik ekler.
        Shift+Home ile o girinti secilir, Delete ile silinir; imlec sutun 0'a doner
        ve satirin gercek girintisi kaynaktan sifirdan yazilir. Boylece merdiven
        etkisi olusmaz. Duz metinde secim bos olur, Delete de en yeni bos satirin
        saginda karakter olmadigindan zararsizdir."""
        windows_api.send_scancode_with_shift(
            windows_api.SC_HOME, extended=True, hold_seconds=KEY_HOLD_SECONDS
        )
        windows_api.send_scancode_key(
            windows_api.SC_DELETE, extended=True, hold_seconds=KEY_HOLD_SECONDS
        )

    def _wait_for_modifier_release(self, cancel_event: Event | None) -> None:
        """Kullanicinin elinde kalmis Ctrl/Alt/Shift/Win varsa birakmasini bekler,
        sonra guvence icin keyup gonderir. Basili bir Ctrl, yazilan her karakteri
        kisayola cevirir."""
        deadline = time.perf_counter() + MODIFIER_RELEASE_TIMEOUT_SECONDS
        while windows_api.held_modifier_keys():
            self._ensure_not_cancelled(cancel_event)
            if time.perf_counter() >= deadline:
                break
            time.sleep(0.02)

        windows_api.release_modifier_keys()

    def _wait(self, seconds: float, cancel_event: Event | None) -> None:
        if seconds <= 0:
            return

        deadline = time.perf_counter() + seconds
        while True:
            self._ensure_not_cancelled(cancel_event)
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return
            if remaining > 0.0015:
                time.sleep(min(remaining - 0.001, 0.02))
                continue
            windows_api.precise_sleep(remaining)
            return

    def _ensure_runnable(
        self,
        cancel_event: Event | None,
        focus_guard: FocusGuard | None,
    ) -> None:
        self._ensure_not_cancelled(cancel_event)

        if focus_guard is not None and not focus_guard():
            raise TypingCancelled("Odak değişti, yazma durduruldu.")

    def _ensure_not_cancelled(self, cancel_event: Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise TypingCancelled("İşlem durduruldu.")
