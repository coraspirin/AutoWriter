# powered by mucahid erdogan
from __future__ import annotations

import gc
import time
import unicodedata
from threading import Event
from typing import Callable

from app.config import (
    CLEAR_AUTO_INDENT_DEFAULT,
    PROGRESS_EMIT_INTERVAL_SECONDS,
    SAFE_PROFILE,
    TARGET_LAYOUT_DEFAULT,
    TARGET_LAYOUTS,
    TYPE_CPS_MIN,
    TypingProfile,
)
from app.services.exceptions import TypingCancelled
from app.services import windows_api

ProgressCallback = Callable[[int, int], None]
FocusGuard = Callable[[], bool]

MODIFIER_RELEASE_TIMEOUT_SECONDS = 2.0


class TextTypingService:
    def __init__(self) -> None:
        # Zamanlama her zaman Guvenli profille yapilir (mod secimi yok).
        self._profile: TypingProfile = SAFE_PROFILE
        self._cps = self._profile.cps_default
        self._clear_indent = CLEAR_AUTO_INDENT_DEFAULT
        self._target_layout = TARGET_LAYOUT_DEFAULT

    def set_target_layout(self, key: str) -> None:
        self._target_layout = key if key in TARGET_LAYOUTS else TARGET_LAYOUT_DEFAULT

    def set_speed(self, cps: int) -> None:
        self._cps = min(max(TYPE_CPS_MIN, cps), self._profile.cps_max)

    def set_clear_auto_indent(self, enabled: bool) -> None:
        self._clear_indent = enabled

    def type_text(
        self,
        text: str,
        cancel_event: Event | None = None,
        progress_callback: ProgressCallback | None = None,
        focus_guard: FocusGuard | None = None,
    ) -> None:
        # PDF/web/macOS'tan kopyalanan metinde "ç" cogu zaman "c" + U+0327
        # (birlesen cengel) olarak gelir. Birlesen isaret klavyede olmadigindan
        # Unicode (VK_PACKET) ile gider ve RDP'de bozulur. NFC tek karaktere birlestirir.
        text = unicodedata.normalize("NFC", text)
        if not text:
            return

        # Ayarlar yazma ortasinda degisirse tutarsizlik olmasin diye sabitlenir.
        profile = self._profile
        clear_indent = self._clear_indent
        interval_seconds = 1.0 / max(1, self._cps)
        _label, layout_klid = TARGET_LAYOUTS[self._target_layout]

        # Cop toplayici yazma ortasinda calisirsa karakter araliginda ms'lik
        # sicrama olur (RDP'de kayip kaynagi). Yazma surece kapali tutulur.
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            self._type_loop(
                text, layout_klid, profile, clear_indent, interval_seconds,
                cancel_event, progress_callback, focus_guard,
            )
        finally:
            # Hata/iptal ne olursa olsun bizim bastigimiz Shift/AltGr basili kalmasin.
            windows_api.release_injected_modifiers()
            if gc_was_enabled:
                gc.enable()

    def _type_loop(
        self,
        text: str,
        layout_klid: str | None,
        profile: TypingProfile,
        clear_indent: bool,
        interval_seconds: float,
        cancel_event: Event | None,
        progress_callback: ProgressCallback | None,
        focus_guard: FocusGuard | None,
    ) -> None:
        total_characters = len(text)
        last_progress_emit = 0.0

        with windows_api.TargetLayout(layout_klid) as keyboard_layout, windows_api.TimerResolution():
            dead_keys = windows_api.detect_dead_keys(set(text), keyboard_layout)
            self._wait_for_modifier_release(cancel_event)

            # Mutlak zaman cizelgesi: Python ve SendInput'un karakter basina
            # harcadigi sure bir sonraki beklemeden dusulur, birikmez.
            next_send = time.perf_counter()

            for index, character in enumerate(text, start=1):
                self._ensure_runnable(cancel_event, focus_guard)
                self._wait_until(next_send, cancel_event)

                extra_delay = self._send_character(
                    character, keyboard_layout, dead_keys, profile, clear_indent
                )

                if profile.burst_size and index % profile.burst_size == 0:
                    extra_delay += profile.burst_pause_seconds

                now = time.perf_counter()
                if progress_callback is not None and (
                    index == total_characters
                    or now - last_progress_emit >= PROGRESS_EMIT_INTERVAL_SECONDS
                ):
                    progress_callback(index, total_characters)
                    last_progress_emit = now

                # Geride kalindiysa (ornegin SendInput tekrar denemesi) kaybedilen
                # sureyi telafi etmek icin art arda yigin gonderme; simdiden say.
                next_send = max(next_send + interval_seconds, now) + extra_delay

    def _send_character(
        self,
        character: str,
        keyboard_layout: int,
        dead_keys: set[str],
        profile: TypingProfile,
        clear_indent: bool,
    ) -> float:
        hold = profile.key_hold_seconds

        if character == "\n":
            windows_api.send_scancode_key(windows_api.SC_RETURN, hold_seconds=hold)
            if clear_indent:
                # Kod editorlerinin otomatik girintisini temizle: metin
                # kutusundaki neyse birebir o yazilsin, merdiven olusmasin.
                self._clear_auto_indent(hold)
            return profile.line_break_extra_seconds

        if character == "\t":
            windows_api.send_scancode_key(windows_api.SC_TAB, hold_seconds=hold)
            return 0.0

        if windows_api.send_character_as_scancode(character, keyboard_layout, hold):
            # Olu tus (^ ~ ` ´): commit boslugu gonder ki aksan standalone cozulsun
            # ve metindeki gercek bosluk yutulmasin.
            if character in dead_keys:
                windows_api.send_scancode_key(windows_api.SC_SPACE, hold_seconds=hold)
            return 0.0

        # Duzende olmayan nadir karakterler (emoji vb.) icin son care.
        windows_api.send_unicode_character(character, hold)
        return 0.0

    def _clear_auto_indent(self, hold: float) -> None:
        """Kod editorleri Enter'dan sonra onceki satirin girintisini otomatik ekler.
        Shift+Home ile o girinti secilir, Delete ile silinir; imlec sutun 0'a doner
        ve satirin gercek girintisi kaynaktan sifirdan yazilir. Boylece merdiven
        etkisi olusmaz. Duz metinde secim bos olur, Delete de en yeni bos satirin
        saginda karakter olmadigindan zararsizdir."""
        windows_api.send_scancode_with_shift(
            windows_api.SC_HOME, extended=True, hold_seconds=hold
        )
        windows_api.send_scancode_key(
            windows_api.SC_DELETE, extended=True, hold_seconds=hold
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

    def _wait_until(self, deadline: float, cancel_event: Event | None) -> None:
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return
            if remaining > 0.0015:
                self._ensure_not_cancelled(cancel_event)
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
