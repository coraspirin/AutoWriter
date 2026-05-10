from __future__ import annotations

from threading import Event

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import (
    APP_NAME,
    COUNTDOWN_SECONDS,
    TYPE_DELAY_MAX_SECONDS,
    TYPE_DELAY_MIN_SECONDS,
    TYPE_SPEED_SLIDER_MAX,
)
from app.services.exceptions import TypingCancelled
from app.services.typing_service import TextTypingService
from app.ui.countdown_overlay import CountdownOverlay
from app.ui.editor_window import EditorWindow


class TypingWorker(QObject):
    finished = Signal(bool, str, bool)

    def __init__(
        self,
        typing_service: TextTypingService,
        text: str,
        browser_compatible: bool,
        cancel_event: Event,
    ) -> None:
        super().__init__()
        self._typing_service = typing_service
        self._text = text
        self._browser_compatible = browser_compatible
        self._cancel_event = cancel_event

    @Slot()
    def run(self) -> None:
        try:
            self._typing_service.type_text(
                self._text,
                self._browser_compatible,
                self._cancel_event,
            )
        except TypingCancelled as exc:
            self.finished.emit(False, str(exc), True)
            return
        except Exception as exc:  # pragma: no cover
            self.finished.emit(False, str(exc), False)
            return

        self.finished.emit(True, "Yazma işlemi tamamlandı", False)


class WindowApplication(QObject):
    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._typing_service = TextTypingService()
        self._editor_window = EditorWindow()
        self._editor_window.run_requested.connect(self._handle_run_requested)
        self._editor_window.speed_changed.connect(self._handle_speed_changed)
        self._editor_window.stop_requested.connect(self.stop_operation)
        self._editor_window.close_requested.connect(self.exit_application)

        self._countdown_overlay = CountdownOverlay()
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._advance_countdown)

        self._typing_thread: QThread | None = None
        self._typing_worker: TypingWorker | None = None
        self._cancel_event = Event()
        self._typing_in_progress = False
        self._countdown_in_progress = False
        self._countdown_remaining = 0
        self._pending_text = ""
        self._pending_browser_mode = True
        self._pending_exit = False

        self._editor_window.set_speed_value(10)
        self._apply_speed_slider_value(10)

    def start(self) -> None:
        self._editor_window.show_normal()

    @Slot(int)
    def _handle_speed_changed(self, value: int) -> None:
        self._apply_speed_slider_value(value)

    def _apply_speed_slider_value(self, value: int) -> None:
        ratio = value / max(TYPE_SPEED_SLIDER_MAX, 1)
        delay_seconds = TYPE_DELAY_MIN_SECONDS + (
            (TYPE_DELAY_MAX_SECONDS - TYPE_DELAY_MIN_SECONDS) * ratio
        )
        line_break_delay_seconds = max(0.2, delay_seconds * 2)
        self._typing_service.set_timing(delay_seconds, line_break_delay_seconds)

    @Slot(str, bool)
    def _handle_run_requested(self, text: str, browser_compatible: bool) -> None:
        if self._typing_in_progress or self._countdown_in_progress:
            self._editor_window.set_busy(True, "Bir yazma işlemi zaten devam ediyor.")
            return

        if not text:
            self._editor_window.set_busy(False, "Önce yazılacak metni girin.")
            self._editor_window.show_normal()
            return

        self._pending_text = text
        self._pending_browser_mode = browser_compatible
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
        self._editor_window.set_busy(True, "Yazılıyor...")
        self._start_typing(self._pending_text, self._pending_browser_mode)

    def _start_typing(self, text: str, browser_compatible: bool) -> None:
        self._cancel_event.clear()
        self._typing_thread = QThread(self)
        self._typing_worker = TypingWorker(
            self._typing_service,
            text,
            browser_compatible,
            self._cancel_event,
        )
        self._typing_worker.moveToThread(self._typing_thread)

        self._typing_thread.started.connect(self._typing_worker.run)
        self._typing_worker.finished.connect(self._finish_typing)
        self._typing_worker.finished.connect(self._typing_thread.quit)
        self._typing_worker.finished.connect(self._typing_worker.deleteLater)
        self._typing_thread.finished.connect(self._typing_thread.deleteLater)
        self._typing_thread.finished.connect(self._clear_worker_references)

        self._typing_thread.start()

    @Slot(bool, str, bool)
    def _finish_typing(self, success: bool, message: str, cancelled: bool) -> None:
        self._typing_in_progress = False
        self._pending_text = ""
        self._cancel_event.clear()

        if self._pending_exit:
            self._quit_application()
            return

        if cancelled:
            self._editor_window.set_busy(False, "İşlem durduruldu.")
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
        self._editor_window.prepare_for_exit()
        self._qt_app.quit()
