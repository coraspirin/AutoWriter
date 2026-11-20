from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

WindowHandle = int

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
winmm = ctypes.WinDLL("winmm", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0
MAPVK_VK_TO_VSC_EX = 4

VK_SPACE = 0x20

# LoadKeyboardLayout: kabuga (dil cubuguna) haber verme.
KLF_NOTELLSHELL = 0x00000080

SW_RESTORE = 9

VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C

# Donanim scan-code'lari (set 1). Enter/Tab/Home/Delete browser RDP uyumu icin
# gercek scan-code olarak gonderilir. Home/Delete "extended" tuslardir.
SC_TAB = 0x0F
SC_RETURN = 0x1C
SC_LSHIFT = 0x2A
SC_HOME = 0x47
SC_DELETE = 0x53
# Sag Alt (AltGr) scan-code'u; extended tus olarak gonderilir.
SC_RMENU = 0x38
SC_SPACE = 0x39

WM_HOTKEY = 0x0312

# VkKeyScanEx modifier maskesi: bit0 = Shift, bit1 = Ctrl, bit2 = Alt.
VKKS_SHIFT = 0b001
VKKS_CTRL_ALT = 0b110

SEND_INPUT_RETRIES = 3
SEND_INPUT_RETRY_DELAY_SECONDS = 0.01

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

user32.GetKeyboardLayoutList.argtypes = (ctypes.c_int, ctypes.POINTER(wintypes.HKL))
user32.GetKeyboardLayoutList.restype = ctypes.c_int

user32.LoadKeyboardLayoutW.argtypes = (wintypes.LPCWSTR, wintypes.UINT)
user32.LoadKeyboardLayoutW.restype = wintypes.HKL

user32.UnloadKeyboardLayout.argtypes = (wintypes.HKL,)
user32.UnloadKeyboardLayout.restype = wintypes.BOOL

user32.VkKeyScanExW.argtypes = (wintypes.WCHAR, wintypes.HKL)
user32.VkKeyScanExW.restype = ctypes.c_short

user32.MapVirtualKeyExW.argtypes = (wintypes.UINT, wintypes.UINT, wintypes.HKL)
user32.MapVirtualKeyExW.restype = wintypes.UINT

user32.ToUnicodeEx.argtypes = (
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_ubyte),
    wintypes.LPWSTR,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.HKL,
)
user32.ToUnicodeEx.restype = ctypes.c_int

user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short

user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
user32.FindWindowW.restype = wintypes.HWND

user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsWindow.argtypes = (wintypes.HWND,)
user32.IsWindow.restype = wintypes.BOOL
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL

user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
user32.UnregisterHotKey.restype = wintypes.BOOL

winmm.timeBeginPeriod.argtypes = (wintypes.UINT,)
winmm.timeBeginPeriod.restype = wintypes.UINT
winmm.timeEndPeriod.argtypes = (wintypes.UINT,)
winmm.timeEndPeriod.restype = wintypes.UINT


def get_keyboard_layout() -> int:
    return user32.GetKeyboardLayout(0)


def keyboard_layout_list() -> list[int]:
    count = user32.GetKeyboardLayoutList(0, None)
    if count <= 0:
        return []
    buffer = (wintypes.HKL * count)()
    count = user32.GetKeyboardLayoutList(count, buffer)
    return [int(handle or 0) for handle in buffer[:count]]


class TargetLayout:
    """Yazma suresince hedef klavye duzenini saglar. klid None ise bu bilgisayarin
    duzeni kullanilir. Duzen sistemde yuklu degilse KLF_ACTIVATE OLMADAN yuklenir
    (kullanicinin aktif duzeni degismez) ve cikista geri kaldirilir; boylece dil
    cubuguna kalici bir duzen eklenmez."""

    def __init__(self, klid: str | None) -> None:
        self._klid = klid
        self._handle = 0
        self._unload_on_exit = False

    def __enter__(self) -> int:
        if self._klid is None:
            self._handle = get_keyboard_layout()
            return self._handle

        loaded_before = set(keyboard_layout_list())
        handle = int(user32.LoadKeyboardLayoutW(self._klid, KLF_NOTELLSHELL) or 0)
        if not handle:
            # Yuklenemezse yerel duzenle devam et; yazma tamamen durmasin.
            self._handle = get_keyboard_layout()
            return self._handle

        self._handle = handle
        self._unload_on_exit = handle not in loaded_before
        return handle

    def __exit__(self, *_: object) -> None:
        if self._unload_on_exit and self._handle:
            user32.UnloadKeyboardLayout(wintypes.HKL(self._handle))


def detect_dead_keys(characters: set[str], keyboard_layout: int) -> set[str]:
    """Verilen karakterlerden hangileri bu klavye duzeninde olu tus (dead key)
    tespit eder. Turkce Q'da ^ ~ ` ´ olu tustur: bir bosluk gelince o bosluk
    aksani standalone'a cevirmek icin tuketilir ve kaybolur. Cagiran taraf bu
    karakterlerden sonra bir "commit" boslugu gonderip gercek boslugu korur."""
    dead: set[str] = set()
    key_state = (ctypes.c_ubyte * 256)()
    buffer = ctypes.create_unicode_buffer(8)

    for character in characters:
        scan_result = user32.VkKeyScanExW(character, keyboard_layout)
        if scan_result == -1:
            continue

        virtual_key = scan_result & 0xFF
        modifier_state = (scan_result >> 8) & 0xFF
        scan_code = user32.MapVirtualKeyExW(virtual_key, MAPVK_VK_TO_VSC, keyboard_layout)

        ctypes.memset(key_state, 0, 256)
        if modifier_state & VKKS_SHIFT:
            key_state[VK_SHIFT] = 0x80
        if modifier_state & 0b010:
            key_state[VK_CONTROL] = 0x80
        if modifier_state & 0b100:
            key_state[VK_MENU] = 0x80

        result = user32.ToUnicodeEx(
            virtual_key, scan_code, key_state, buffer, len(buffer), 0, keyboard_layout
        )
        if result < 0:
            dead.add(character)

        # ToUnicodeEx olu tus durumunu cekirdek tamponunda birakir; sonraki gercek
        # yazimi bozmamak icin bosluk vurusuyla tamponu bosaltiyoruz.
        ctypes.memset(key_state, 0, 256)
        user32.ToUnicodeEx(
            VK_SPACE,
            user32.MapVirtualKeyExW(VK_SPACE, MAPVK_VK_TO_VSC, keyboard_layout),
            key_state,
            buffer,
            len(buffer),
            0,
            keyboard_layout,
        )

    return dead


class TimerResolution:
    """time.sleep() Windows'ta varsayilan ~15.6 ms cozunurlukle uyur; bu da
    karakter araliklarini duzensizlestirir ve RDP'de kayba yol acar. Yazma
    boyunca sistem zamanlayici cozunurlugunu 1 ms'e ceker."""

    def __enter__(self) -> "TimerResolution":
        winmm.timeBeginPeriod(1)
        return self

    def __exit__(self, *_: object) -> None:
        winmm.timeEndPeriod(1)


def precise_sleep(seconds: float) -> None:
    if seconds <= 0:
        return

    deadline = time.perf_counter() + seconds
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return
        if remaining > 0.0015:
            time.sleep(remaining - 0.001)
            continue
        while time.perf_counter() < deadline:
            pass
        return


def send_unicode_character(character: str, hold_seconds: float = 0.0) -> None:
    """Karakteri KEYEVENTF_UNICODE (VK_PACKET) ile gonderir. Klavye duzeninden
    bagimsizdir ve hicbir modifier basmadigi icin kisayol tetikleyemez."""
    encoded = character.encode("utf-16-le")
    code_units = [
        int.from_bytes(encoded[index : index + 2], "little")
        for index in range(0, len(encoded), 2)
    ]

    # Surrogate ciftleri tek SendInput cagrisinda ardisik gitmek zorunda.
    down_events = [
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE, 0, 0))
        for unit in code_units
    ]
    up_events = [
        INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0),
        )
        for unit in code_units
    ]

    _send_input(down_events)
    precise_sleep(hold_seconds)
    _send_input(up_events)


def _scan_input(scan_code: int, extended: bool, keyup: bool) -> INPUT:
    flags = KEYEVENTF_SCANCODE
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if keyup:
        flags |= KEYEVENTF_KEYUP
    return INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan_code, flags, 0, 0))


def send_scancode_key(scan_code: int, extended: bool = False, hold_seconds: float = 0.0) -> None:
    _send_input([_scan_input(scan_code, extended, keyup=False)])
    precise_sleep(hold_seconds)
    _send_input([_scan_input(scan_code, extended, keyup=True)])


def send_scancode_with_shift(
    scan_code: int,
    extended: bool = False,
    hold_seconds: float = 0.0,
) -> None:
    """Shift basiliyken bir scan-code tusu gonderir. Otomatik girinti temizleme
    adiminda Shift+Home icin kullanilir."""
    _send_input(
        [
            _scan_input(SC_LSHIFT, extended=False, keyup=False),
            _scan_input(scan_code, extended, keyup=False),
        ]
    )
    precise_sleep(hold_seconds)
    _send_input(
        [
            _scan_input(scan_code, extended, keyup=True),
            _scan_input(SC_LSHIFT, extended=False, keyup=True),
        ]
    )


def send_character_as_scancode(
    character: str,
    keyboard_layout: int,
    hold_seconds: float = 0.0,
) -> bool:
    """Karakteri donanim scan-code'u olarak gonderir. Browser tabanli (HTML5)
    RDP istemcileri klavyeyi gercek tus olaylarindan okur; Unicode (VK_PACKET)
    enjeksiyonunu goremez, bu yuzden scan-code sart.

    AltGr karakterleri (Turkce Q klavyede @ # $ { } [ ] \\ | ~): SAG ALT (AltGr)
    scan-code'u ile gonderilir, Ctrl BASILMAZ. Uzak makinenin surucusu sag Alt'i
    AltGr olarak isleyip karakteri kendisi uretir; Ctrl gonderilmedigi icin hedef
    bunu Ctrl+Alt kisayolu degil, karakter girisi olarak gorur. Fiziksel AltGr'nin
    yaptigi budur. Duzende olmayan karakterlerde (-1) False doner -> Unicode fallback."""
    scan_result = user32.VkKeyScanExW(character, keyboard_layout)
    if scan_result == -1:
        return False

    virtual_key = scan_result & 0xFF
    modifier_state = (scan_result >> 8) & 0xFF

    scan_code = user32.MapVirtualKeyExW(virtual_key, MAPVK_VK_TO_VSC_EX, keyboard_layout)
    if not scan_code:
        return False

    needs_shift = bool(modifier_state & VKKS_SHIFT)
    needs_altgr = bool(modifier_state & VKKS_CTRL_ALT)

    down_events: list[INPUT] = []
    up_events: list[INPUT] = []

    if needs_altgr:
        down_events.append(_scan_input(SC_RMENU, extended=True, keyup=False))
        up_events.insert(0, _scan_input(SC_RMENU, extended=True, keyup=True))
    if needs_shift:
        down_events.append(_scan_input(SC_LSHIFT, extended=False, keyup=False))
        up_events.insert(0, _scan_input(SC_LSHIFT, extended=False, keyup=True))

    down_events.append(_scan_input(scan_code, extended=False, keyup=False))
    up_events.insert(0, _scan_input(scan_code, extended=False, keyup=True))

    _send_input(down_events)
    precise_sleep(hold_seconds)
    _send_input(up_events)
    return True


def held_modifier_keys() -> list[int]:
    return [
        virtual_key
        for virtual_key in (VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)
        if user32.GetAsyncKeyState(virtual_key) & 0x8000
    ]


def release_modifier_keys() -> None:
    """Yazma baslarken kullanicinin elinde kalmis modifier tuslarini birakir.
    Basili bir Ctrl, sonraki her karakteri kisayola cevirir."""
    events = [
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(virtual_key, 0, KEYEVENTF_KEYUP, 0, 0))
        for virtual_key in held_modifier_keys()
    ]
    if events:
        _send_input(events)


def find_window_by_title(title: str) -> WindowHandle:
    return int(user32.FindWindowW(None, title) or 0)


def get_foreground_window() -> WindowHandle:
    return int(user32.GetForegroundWindow() or 0)


def is_window(window_handle: WindowHandle) -> bool:
    return bool(user32.IsWindow(wintypes.HWND(window_handle)))


def restore_window(window_handle: WindowHandle) -> bool:
    handle = wintypes.HWND(window_handle)
    if user32.IsIconic(handle):
        user32.ShowWindow(handle, SW_RESTORE)

    return bool(user32.SetForegroundWindow(handle))


def register_hotkey(window_handle: WindowHandle, hotkey_id: int, virtual_key: int) -> bool:
    return bool(user32.RegisterHotKey(wintypes.HWND(window_handle), hotkey_id, 0, virtual_key))


def unregister_hotkey(window_handle: WindowHandle, hotkey_id: int) -> None:
    user32.UnregisterHotKey(wintypes.HWND(window_handle), hotkey_id)


def _send_input(events: list[INPUT]) -> None:
    if not events:
        return

    payload = (INPUT * len(events))(*events)

    # SendInput, ALT+TAB anlarinda veya yetkili bir pencere ondeyken (UIPI)
    # gecici olarak engellenebilir. Tek denemede pes etmek yazmayi ortasinda
    # kesiyor; kisa gecikmelerle tekrar deniyoruz.
    for attempt in range(SEND_INPUT_RETRIES):
        ctypes.set_last_error(0)
        sent = user32.SendInput(len(payload), payload, ctypes.sizeof(INPUT))
        if sent == len(payload):
            return

        if attempt < SEND_INPUT_RETRIES - 1:
            time.sleep(SEND_INPUT_RETRY_DELAY_SECONDS)

    error_code = ctypes.get_last_error()
    if error_code:
        raise RuntimeError(f"Windows klavye girdisi gönderilemedi. Hata kodu: {error_code}")

    raise RuntimeError("Windows klavye girdisi gönderilemedi.")
