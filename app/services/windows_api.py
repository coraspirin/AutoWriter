from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

WindowHandle = int

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
SW_RESTORE = 9
VK_RETURN = 0x0D
VK_TAB = 0x09
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

user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.AttachThreadInput.argtypes = (wintypes.DWORD, wintypes.DWORD, wintypes.BOOL)
user32.AttachThreadInput.restype = wintypes.BOOL

user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL

user32.BringWindowToTop.argtypes = (wintypes.HWND,)
user32.BringWindowToTop.restype = wintypes.BOOL

user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL

user32.IsWindow.argtypes = (wintypes.HWND,)
user32.IsWindow.restype = wintypes.BOOL

user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL


def get_foreground_window() -> WindowHandle | None:
    hwnd = int(user32.GetForegroundWindow())
    return hwnd or None


def is_window(hwnd: WindowHandle) -> bool:
    return bool(user32.IsWindow(hwnd))


def restore_window(hwnd: WindowHandle) -> bool:
    if not hwnd or not is_window(hwnd):
        return False

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)

    current_foreground = get_foreground_window()
    current_thread = (
        user32.GetWindowThreadProcessId(current_foreground, None) if current_foreground else 0
    )
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    app_thread = kernel32.GetCurrentThreadId()

    attached_threads: list[tuple[int, int]] = []

    def attach_thread(source_thread: int, destination_thread: int) -> None:
        if (
            source_thread
            and destination_thread
            and source_thread != destination_thread
            and user32.AttachThreadInput(source_thread, destination_thread, True)
        ):
            attached_threads.append((source_thread, destination_thread))

    attach_thread(current_thread, app_thread)
    attach_thread(target_thread, app_thread)

    user32.BringWindowToTop(hwnd)
    restored = bool(user32.SetForegroundWindow(hwnd))

    for source_thread, destination_thread in reversed(attached_threads):
        user32.AttachThreadInput(source_thread, destination_thread, False)

    return restored


def send_text_with_send_input(
    text: str,
    delay_seconds: float,
    line_break_delay_seconds: float,
) -> None:
    for character in text:
        if character == "\n":
            _send_virtual_key(VK_RETURN)
            _sleep(line_break_delay_seconds)
        elif character == "\t":
            _send_virtual_key(VK_TAB)
            _sleep(delay_seconds)
        else:
            _send_unicode_character(character)
            _sleep(delay_seconds)


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


def _send_input(inputs: ctypes.Array[INPUT]) -> None:
    ctypes.set_last_error(0)
    sent = user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        error_code = ctypes.get_last_error()
        if error_code:
            raise RuntimeError(f"Windows klavye girdisi gönderilemedi. Hata kodu: {error_code}")

        raise RuntimeError("Windows klavye girdisi gönderilemedi.")


def _sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
