from __future__ import annotations

import time

from app.config import LINE_BREAK_DELAY_SECONDS, TYPE_DELAY_SECONDS
from app.services.windows_api import send_text_with_send_input

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

    def type_text(self, text: str) -> None:
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

        if keyboard is not None:
            try:
                self._type_with_keyboard(normalized_text)
                return
            except Exception:
                pass

        send_text_with_send_input(
            normalized_text,
            self._delay_seconds,
            self._line_break_delay_seconds,
        )

    def _type_with_keyboard(self, text: str) -> None:
        for character in text:
            if character == "\n":
                keyboard.send("enter")
                self._sleep(self._line_break_delay_seconds)
            elif character == "\t":
                keyboard.send("tab")
                self._sleep(self._delay_seconds)
            else:
                keyboard.write(character, delay=0, exact=True)
                self._sleep(self._delay_seconds)

    def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)
