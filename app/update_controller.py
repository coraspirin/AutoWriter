# powered by mucahid erdogan
from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from app.config import APP_NAME, APP_VERSION, UPDATE_CHECK_DELAY_MS
from app.services import updater
from app.ui.editor_window import EditorWindow

RELEASE_NOTES_MAX_CHARS = 800


class UpdateController(QObject):
    """Acilista GitHub Releases'i kontrol eder; yeni surum varsa sag ustteki
    Guncelle butonunu gosterir. Ag islemleri arka plan thread'inde yapilir;
    sonuclar sinyallerle UI thread'ine doner (Qt cross-thread sinyalleri
    otomatik olarak kuyruga alir)."""

    _found = Signal(object)
    _up_to_date = Signal()
    _check_failed = Signal()
    _progress = Signal(int, int)
    _downloaded = Signal(str)
    _download_failed = Signal(str)

    def __init__(
        self,
        editor_window: EditorWindow,
        is_busy: Callable[[], bool],
        request_quit: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._editor_window = editor_window
        self._is_busy = is_busy
        self._request_quit = request_quit
        self._release: updater.ReleaseInfo | None = None
        self._downloading = False
        self._last_percent = -1

        self._checking = False
        self._found.connect(self._handle_found)
        self._up_to_date.connect(self._handle_up_to_date)
        self._check_failed.connect(self._handle_check_failed)
        self._editor_window.check_updates_requested.connect(self.check_now)
        self._progress.connect(self._handle_progress)
        self._downloaded.connect(self._handle_downloaded)
        self._download_failed.connect(self._handle_download_failed)
        self._editor_window.update_requested.connect(self._handle_update_requested)

    def schedule_check(self) -> None:
        QTimer.singleShot(UPDATE_CHECK_DELAY_MS, self.check_now)

    @Slot()
    def check_now(self) -> None:
        if self._checking or self._downloading:
            return
        self._checking = True
        self._editor_window.set_update_check_state("checking")
        threading.Thread(target=self._check_worker, daemon=True).start()

    # --- Arka plan ---------------------------------------------------------

    def _check_worker(self) -> None:
        try:
            release = updater.check_for_update()
        except updater.UpdateError:
            self._check_failed.emit()  # Internet yok, GitHub erisilemiyor...
            return
        if release is None:
            self._up_to_date.emit()
        else:
            self._found.emit(release)

    def _download_worker(self, release: updater.ReleaseInfo) -> None:
        try:
            path = updater.download_asset(release, progress_callback=self._progress.emit)
        except updater.UpdateError as exc:
            self._download_failed.emit(str(exc))
            return
        self._downloaded.emit(str(path))

    # --- UI thread ---------------------------------------------------------

    @Slot()
    def _handle_up_to_date(self) -> None:
        self._checking = False
        self._release = None
        self._editor_window.set_update_check_state("up_to_date")

    @Slot()
    def _handle_check_failed(self) -> None:
        self._checking = False
        if self._release is not None:
            # Daha once yeni surum bulunduysa onu gostermeye devam et.
            self._editor_window.show_update_available(self._release.version)
            return
        self._editor_window.set_update_check_state("failed")

    @Slot(object)
    def _handle_found(self, release: updater.ReleaseInfo) -> None:
        self._checking = False
        self._release = release
        self._editor_window.show_update_available(release.version)

    @Slot()
    def _handle_update_requested(self) -> None:
        release = self._release
        if release is None or self._downloading:
            return

        if self._is_busy():
            self._editor_window.set_status("Güncellemek için önce yazma işleminin bitmesini bekleyin.")
            return

        if not updater.is_frozen():
            # Kaynaktan calisiyoruz: exe degistirilemez, release sayfasini ac.
            QDesktopServices.openUrl(QUrl(release.page_url))
            return

        notes = release.notes
        if len(notes) > RELEASE_NOTES_MAX_CHARS:
            notes = notes[:RELEASE_NOTES_MAX_CHARS].rstrip() + "…"
        message = (
            f"Yeni sürüm: v{release.version}\nŞu anki sürüm: v{APP_VERSION}\n\n"
            + (f"{notes}\n\n" if notes else "")
            + "İndirilip kurulsun mu? Uygulama kapanıp yeni sürümle yeniden açılacak."
        )
        answer = QMessageBox.question(
            self._editor_window,
            f"{APP_NAME} – Güncelleme",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return

        self._downloading = True
        self._last_percent = -1
        self._editor_window.set_update_state("İndiriliyor… %0", enabled=False)
        threading.Thread(target=self._download_worker, args=(release,), daemon=True).start()

    @Slot(int, int)
    def _handle_progress(self, received: int, total: int) -> None:
        if total <= 0:
            return
        percent = int(received * 100 / total)
        if percent != self._last_percent:
            self._last_percent = percent
            self._editor_window.set_update_state(f"İndiriliyor… %{percent}", enabled=False)

    @Slot(str)
    def _handle_downloaded(self, path: str) -> None:
        self._editor_window.set_update_state("Kuruluyor…", enabled=False)
        try:
            from pathlib import Path

            updater.install_and_restart(Path(path))
        except updater.UpdateError as exc:
            self._handle_download_failed(str(exc))
            return

        self._request_quit()

    @Slot(str)
    def _handle_download_failed(self, message: str) -> None:
        self._downloading = False
        release = self._release
        if release is not None:
            self._editor_window.show_update_available(release.version)
        QMessageBox.warning(
            self._editor_window,
            f"{APP_NAME} – Güncelleme",
            f"{message}\n\nYeni sürümü elle de indirebilirsiniz:\n"
            + (release.page_url if release else ""),
        )
