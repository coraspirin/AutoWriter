# powered by mucahid erdogan
from __future__ import annotations

from threading import Event

from PySide6.QtCore import QObject, QSettings, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import (
    APP_NAME,
    COUNTDOWN_SECONDS,
    HOTKEY_ID_STOP,
    HOTKEY_STOP_LABEL,
    CLEAR_AUTO_INDENT_DEFAULT,
    EXPAND_TABS_DEFAULT,
    TAB_WIDTH_CHOICES,
    TAB_WIDTH_DEFAULT,
    TARGET_LAYOUT_DEFAULT,
    TARGET_LAYOUTS,
    TYPE_CPS_DEFAULT,
    TYPE_CPS_MAX,
    TYPE_CPS_MIN,
    VK_F10,
)
from app.services.exceptions import TypingCancelled
from app.services.focus_tracker import FocusTracker
from app.services.hotkeys import GlobalHotkeys
from app.services.typing_service import TextTypingService
from app.ui.countdown_overlay import CountdownOverlay
from app.ui.editor_window import EditorWindow
from app.update_controller import UpdateController

SETTINGS_ORG = "Coraspirin"
SETTINGS_APP = "AutoWriter"


class TypingWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(bool, str, bool)

    def __init__(
        self,
        typing_service: TextTypingService,
        text: str,
        cancel_event: Event,
        focus_guard,
    ) -> None:
        super().__init__()
        self._typing_service = typing_service
        self._text = text
        self._cancel_event = cancel_event
        self._focus_guard = focus_guard

    @Slot()
    def run(self) -> None:
        try:
            self._typing_service.type_text(
                self._text,
                cancel_event=self._cancel_event,
                progress_callback=self.progress.emit,
                focus_guard=self._focus_guard,
            )
        except TypingCancelled as exc:
            self.finished.emit(False, str(exc), True)
            return
        except Exception as exc:  # pragma: no cover - Windows API sinirinda
            self.finished.emit(False, str(exc), False)
            return

        self.finished.emit(True, "Yazma işlemi tamamlandı", False)


class WindowApplication(QObject):
    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._typing_service = TextTypingService()

        self._editor_window = EditorWindow()
        self._countdown_overlay = CountdownOverlay()
        self._focus_tracker = FocusTracker(self)
        self._hotkeys = GlobalHotkeys(self)

        self._cancel_event = Event()
        self._pending_text = ""
        self._typing_in_progress = False
        self._countdown_in_progress = False
        self._countdown_remaining = 0
        self._pending_exit = False
        self._typing_thread: QThread | None = None
        self._typing_worker: TypingWorker | None = None

        self._update_controller = UpdateController(
            self._editor_window,
            is_busy=lambda: self._typing_in_progress or self._countdown_in_progress,
            request_quit=self._quit_application,
            parent=self,
        )

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._advance_countdown)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self._editor_window.run_requested.connect(self._handle_run_requested)
        self._editor_window.stop_requested.connect(self.stop_operation)
        self._editor_window.close_requested.connect(self.exit_application)
        self._editor_window.settings_changed.connect(self._handle_settings_changed)

        self._hotkeys.triggered.connect(self._handle_hotkey)

    def start(self) -> None:
        self._load_preferences()
        self._editor_window.show_normal()
        self._update_controller.schedule_check()

        self._focus_tracker.register_window(self._editor_window)
        self._focus_tracker.register_window(self._countdown_overlay)

        self._qt_app.installNativeEventFilter(self._hotkeys)
        failed = self._hotkeys.register(
            int(self._editor_window.winId()),
            {HOTKEY_ID_STOP: VK_F10},
        )
        if failed:
            self._editor_window.set_busy(
                False,
                f"Uyarı: {HOTKEY_STOP_LABEL} kısayolu başka bir uygulama "
                "tarafından kullanılıyor.",
            )

    # --- Tercihler ---------------------------------------------------------

    def _load_preferences(self) -> None:
        # Eski surumlerden kalan mod tercihi artik kullanilmiyor (hep Guvenli).
        self._settings.remove("mode")

        cps = self._settings.value("cps", TYPE_CPS_DEFAULT, type=int)
        cps = min(max(cps, TYPE_CPS_MIN), TYPE_CPS_MAX)
        clear_indent = self._settings.value(
            "clear_auto_indent", CLEAR_AUTO_INDENT_DEFAULT, type=bool
        )
        expand_tabs = self._settings.value("expand_tabs", EXPAND_TABS_DEFAULT, type=bool)
        tab_width = self._settings.value("tab_width", TAB_WIDTH_DEFAULT, type=int)
        if tab_width not in TAB_WIDTH_CHOICES:
            tab_width = TAB_WIDTH_DEFAULT
        target_layout = self._settings.value("target_layout", TARGET_LAYOUT_DEFAULT, type=str)
        if target_layout not in TARGET_LAYOUTS:
            target_layout = TARGET_LAYOUT_DEFAULT

        self._editor_window.set_speed_value(cps)
        self._editor_window.set_clear_auto_indent(clear_indent)
        self._editor_window.set_expand_tabs(expand_tabs, tab_width)
        self._editor_window.set_target_layout(target_layout)
        self._apply_preferences()

    @Slot()
    def _handle_settings_changed(self) -> None:
        self._apply_preferences()
        self._settings.setValue("cps", self._editor_window.speed_value())
        self._settings.setValue("clear_auto_indent", self._editor_window.clear_auto_indent())
        self._settings.setValue("expand_tabs", self._editor_window.expand_tabs())
        self._settings.setValue("tab_width", self._editor_window.tab_width())
        self._settings.setValue("target_layout", self._editor_window.target_layout())

    def _apply_preferences(self) -> None:
        self._typing_service.set_speed(self._editor_window.speed_value())
        self._typing_service.set_clear_auto_indent(self._editor_window.clear_auto_indent())
        self._typing_service.set_target_layout(self._editor_window.target_layout())

    # --- Yazma akisi -------------------------------------------------------

    @Slot(str)
    def _handle_run_requested(self, text: str) -> None:
        if self._typing_in_progress or self._countdown_in_progress:
            self._editor_window.set_busy(True, "Bir yazma işlemi zaten devam ediyor.")
            return

        # \r\n -> \n disinda metne dokunmuyoruz; girinti dahil birebir yazilir.
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not normalized_text:
            self._editor_window.set_busy(False, "Önce yazılacak metni girin.")
            self._editor_window.show_normal()
            return

        if self._editor_window.expand_tabs():
            # expandtabs sutuna gore hizalar: satir ortasindaki Tab da dogru
            # sayida bosluga donusur.
            normalized_text = normalized_text.expandtabs(self._editor_window.tab_width())

        self._pending_text = normalized_text
        self._begin_countdown()

    def _begin_countdown(self) -> None:
        self._cancel_event.clear()
        self._countdown_in_progress = True
        self._countdown_remaining = COUNTDOWN_SECONDS
        self._editor_window.set_busy(True, f"Geri sayım: {self._countdown_remaining} sn")
        self._countdown_overlay.show_countdown(self._countdown_remaining)
        self._countdown_timer.start()

    @Slot()
    def _advance_countdown(self) -> None:
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._editor_window.set_busy(True, f"Geri sayım: {self._countdown_remaining} sn")
            self._countdown_overlay.show_countdown(self._countdown_remaining)
            return

        self._countdown_timer.stop()
        self._countdown_in_progress = False
        self._countdown_overlay.hide()
        self._typing_in_progress = True
        self._focus_tracker.lock_target()
        self._editor_window.set_busy(True, f"Yazılıyor... ({HOTKEY_STOP_LABEL} durdur)")
        self._start_typing(self._pending_text)

    def _start_typing(self, text: str) -> None:
        self._cancel_event.clear()
        self._editor_window.set_progress(0, len(text), self._editor_window.speed_value())

        self._typing_thread = QThread(self)
        self._typing_worker = TypingWorker(
            self._typing_service,
            text,
            self._cancel_event,
            self._focus_tracker.is_target_focused,
        )
        self._typing_worker.moveToThread(self._typing_thread)

        self._typing_thread.started.connect(self._typing_worker.run)
        self._typing_worker.progress.connect(self._handle_progress)
        self._typing_worker.finished.connect(self._finish_typing)
        self._typing_worker.finished.connect(self._typing_thread.quit)
        self._typing_worker.finished.connect(self._typing_worker.deleteLater)
        self._typing_thread.finished.connect(self._typing_thread.deleteLater)
        self._typing_thread.finished.connect(self._clear_worker_references)

        self._typing_thread.start()

    @Slot(int, int)
    def _handle_progress(self, done: int, total: int) -> None:
        self._editor_window.set_progress(done, total, self._editor_window.speed_value())

    @Slot(bool, str, bool)
    def _finish_typing(self, success: bool, message: str, cancelled: bool) -> None:
        self._typing_in_progress = False
        self._pending_text = ""
        self._cancel_event.clear()
        self._focus_tracker.release_target()
        self._editor_window.clear_progress()

        if self._pending_exit:
            self._quit_application()
            return

        if cancelled:
            self._editor_window.set_busy(False, message)
            return

        if success:
            self._editor_window.set_busy(False, message)
            return

        self._editor_window.set_busy(False, f"Yazma hatası: {message}")
        QMessageBox.critical(self._editor_window, APP_NAME, message)
        self._editor_window.show_normal()

    @Slot()
    def _clear_worker_references(self) -> None:
        self._typing_thread = None
        self._typing_worker = None

    # --- Kontrol -----------------------------------------------------------

    @Slot(int)
    def _handle_hotkey(self, hotkey_id: int) -> None:
        if hotkey_id == HOTKEY_ID_STOP:
            self.stop_operation()

    @Slot()
    def stop_operation(self) -> None:
        if self._countdown_in_progress:
            self._cancel_countdown()
            self._editor_window.set_busy(False, "İşlem durduruldu.")
            return

        if self._typing_in_progress:
            self._cancel_event.set()
            self._editor_window.set_busy(True, "Durduruluyor...")
            return

        self._editor_window.set_busy(False, "Hazır")

    @Slot()
    def exit_application(self) -> None:
        if self._countdown_in_progress:
            self._cancel_countdown()
            self._quit_application()
            return

        if self._typing_in_progress:
            self._pending_exit = True
            self._cancel_event.set()
            self._editor_window.set_busy(True, "Kapatılıyor...")
            return

        self._quit_application()

    def _cancel_countdown(self) -> None:
        self._countdown_timer.stop()
        self._countdown_in_progress = False
        self._countdown_remaining = 0
        self._pending_text = ""
        self._countdown_overlay.hide()

    def _quit_application(self) -> None:
        self._cancel_countdown()
        self._hotkeys.unregister_all()
        self._qt_app.removeNativeEventFilter(self._hotkeys)
        self._editor_window.prepare_for_exit()
        self._qt_app.quit()
