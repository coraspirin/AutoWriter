from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from threading import Event

from app.services.exceptions import TypingCancelled

WindowHandle = int

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
SW_RESTORE = 9
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT

user32.GetKeyboardLayout.argtypes = (wintypes.DWORD,)
user32.GetKeyboardLayout.restype = wintypes.HKL

user32.VkKeyScanExW.argtypes = (wintypes.WCHAR, wintypes.HKL)
user32.VkKeyScanExW.restype = ctypes.c_short


def send_text_with_send_input(
    text: str,
    delay_seconds: float,
    line_break_delay_seconds: float,
    cancel_event: Event | None = None,
) -> None:
    for character in text:
        _ensure_not_cancelled(cancel_event)

        if character == "\n":
            _send_virtual_key(VK_RETURN)
            _sleep(line_break_delay_seconds, cancel_event)
        elif character == "\t":
            _send_virtual_key(VK_TAB)
            _sleep(delay_seconds, cancel_event)
        else:
            _send_unicode_character(character)
            _sleep(delay_seconds, cancel_event)


def send_text_with_virtual_keys(
    text: str,
    delay_seconds: float,
    line_break_delay_seconds: float,
    cancel_event: Event | None = None,
) -> None:
    keyboard_layout = user32.GetKeyboardLayout(0)

    for character in text:
        _ensure_not_cancelled(cancel_event)

        if character == "\n":
            _send_virtual_key(VK_RETURN)
            _sleep(line_break_delay_seconds, cancel_event)
            continue

        if character == "\t":
            _send_virtual_key(VK_TAB)
            _sleep(delay_seconds, cancel_event)
            continue

        key_info = user32.VkKeyScanExW(character, keyboard_layout)
        if key_info == -1:
            _send_unicode_character(character)
            _sleep(delay_seconds, cancel_event)
            continue

        virtual_key = key_info & 0xFF
        shift_state = (key_info >> 8) & 0xFF
        _send_virtual_key_with_modifiers(virtual_key, shift_state)
        _sleep(delay_seconds, cancel_event)


def _send_unicode_character(character: str) -> None:
    encoded = character.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        code_unit = int.from_bytes(encoded[index : index + 2], "little")
        inputs = (INPUT * 2)(
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, code_unit, KEYEVENTF_UNICODE, 0, 0)),
            INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(0, code_unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0),
            ),
        )
        _send_input(inputs)


def _send_virtual_key(virtual_key: int) -> None:
    inputs = (INPUT * 2)(
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(virtual_key, 0, 0, 0, 0)),
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(virtual_key, 0, KEYEVENTF_KEYUP, 0, 0)),
    )
    _send_input(inputs)


def _send_virtual_key_with_modifiers(virtual_key: int, shift_state: int) -> None:
    modifier_order: list[int] = []
    if shift_state & 1:
        modifier_order.append(VK_SHIFT)
    if shift_state & 2:
        modifier_order.append(VK_CONTROL)
    if shift_state & 4:
        modifier_order.append(VK_MENU)

    events: list[INPUT] = []
    for modifier in modifier_order:
        events.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(modifier, 0, 0, 0, 0)))

    events.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(virtual_key, 0, 0, 0, 0)))
    events.append(
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(virtual_key, 0, KEYEVENTF_KEYUP, 0, 0))
    )

    for modifier in reversed(modifier_order):
        events.append(
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(modifier, 0, KEYEVENTF_KEYUP, 0, 0))
        )

    typed_events = (INPUT * len(events))(*events)
    _send_input(typed_events)


def _send_input(inputs: ctypes.Array[INPUT]) -> None:
    ctypes.set_last_error(0)
    sent = user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        error_code = ctypes.get_last_error()
        if error_code:
            raise RuntimeError(f"Windows klavye girdisi gönderilemedi. Hata kodu: {error_code}")

        raise RuntimeError("Windows klavye girdisi gönderilemedi.")


def _sleep(seconds: float, cancel_event: Event | None) -> None:
    if seconds <= 0:
        return

    elapsed = 0.0
    while elapsed < seconds:
        _ensure_not_cancelled(cancel_event)
        step = min(0.05, seconds - elapsed)
        time.sleep(step)
        elapsed += step


def _ensure_not_cancelled(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise TypingCancelled("İşlem durduruldu.")
