# powered by mucahid erdogan
from __future__ import annotations

import time
from threading import Event

from app.config import LINE_BREAK_DELAY_SECONDS, TYPE_DELAY_SECONDS
from app.services.exceptions import TypingCancelled
from app.services.windows_api import send_text_with_send_input, send_text_with_virtual_keys

try:
    import keyboard
except ImportError:  # pragma: no cover - dependency boundary
    keyboard = None


class TextTypingService:
    def __init__(
        self,
        delay_seconds: float = TYPE_DELAY_SECONDS,
        line_break_delay_seconds: float = LINE_BREAK_DELAY_SECONDS,
    ) -> None:
        self._delay_seconds = delay_seconds
        self._line_break_delay_seconds = line_break_delay_seconds

    def set_timing(self, delay_seconds: float, line_break_delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds
        self._line_break_delay_seconds = line_break_delay_seconds

    def type_text(
        self,
        text: str,
        browser_compatible: bool = False,
        cancel_event: Event | None = None,
    ) -> None:
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

        if browser_compatible:
            send_text_with_virtual_keys(
                normalized_text,
                self._delay_seconds,
                self._line_break_delay_seconds,
                cancel_event,
            )
            return

        if keyboard is not None:
            try:
                self._type_with_keyboard(normalized_text, cancel_event)
                return
            except Exception:
                pass

        send_text_with_send_input(
            normalized_text,
            self._delay_seconds,
            self._line_break_delay_seconds,
            cancel_event,
        )

    def _type_with_keyboard(self, text: str, cancel_event: Event | None) -> None:
        for character in text:
            self._ensure_not_cancelled(cancel_event)

            if character == "\n":
                keyboard.send("enter")
                self._sleep(self._line_break_delay_seconds, cancel_event)
            elif character == "\t":
                keyboard.send("tab")
                self._sleep(self._delay_seconds, cancel_event)
            else:
                keyboard.write(character, delay=0, exact=True)
                self._sleep(self._delay_seconds, cancel_event)

    def _sleep(self, seconds: float, cancel_event: Event | None) -> None:
        if seconds <= 0:
            return

        elapsed = 0.0
        while elapsed < seconds:
            self._ensure_not_cancelled(cancel_event)
            step = min(0.05, seconds - elapsed)
            time.sleep(step)
            elapsed += step

    def _ensure_not_cancelled(self, cancel_event: Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise TypingCancelled("İşlem durduruldu.")


