# powered by mucahid erdogan
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    HOTKEY_STOP_LABEL,
    TYPE_CPS_MAX,
    TYPE_CPS_MIN,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)


class EditorWindow(QWidget):
    run_requested = Signal(str)
    stop_requested = Signal()
    close_requested = Signal()
    settings_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self._build_ui()

    # --- Kurulum -----------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)

        root_panel = QWidget(self)
        root_panel.setObjectName("RootPanel")
        root_layout.addWidget(root_panel)

        panel_layout = QVBoxLayout(root_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(16)

        panel_layout.addLayout(self._build_brand(root_panel))

        self._text_edit = QTextEdit(root_panel)
        self._text_edit.setPlaceholderText(
            "Yazdırılacak metni buraya girin. Satırlar ve özel karakterler korunur."
        )
        panel_layout.addWidget(self._text_edit, 1)

        panel_layout.addWidget(self._build_speed_card(root_panel))
        panel_layout.addLayout(self._build_footer(root_panel))

    def _build_brand(self, parent: QWidget) -> QVBoxLayout:
        brand_layout = QVBoxLayout()
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(2)

        brand_label = QLabel("coraspirin", parent)
        brand_label.setObjectName("BrandLabel")
        brand_layout.addWidget(brand_label)

        brand_subtitle = QLabel("Auto Writer", parent)
        brand_subtitle.setObjectName("BrandSubtitle")
        brand_layout.addWidget(brand_subtitle)

        return brand_layout

    def _build_speed_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SpeedCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        speed_header = QHBoxLayout()
        speed_header.setContentsMargins(0, 0, 0, 0)

        speed_title = QLabel("Yazma Hızı", card)
        speed_title.setObjectName("SectionLabel")
        speed_header.addWidget(speed_title)

        self._speed_value_label = QLabel("", card)
        self._speed_value_label.setObjectName("SpeedValueLabel")
        speed_header.addWidget(self._speed_value_label, 0, Qt.AlignRight)

        layout.addLayout(speed_header)

        self._speed_slider = QSlider(Qt.Horizontal, card)
        self._speed_slider.setRange(TYPE_CPS_MIN, TYPE_CPS_MAX)
        self._speed_slider.setSingleStep(1)
        self._speed_slider.setPageStep(5)
        self._speed_slider.valueChanged.connect(self._handle_speed_changed)
        layout.addWidget(self._speed_slider)

        speed_hint = QHBoxLayout()
        speed_hint.setContentsMargins(0, 0, 0, 0)
        speed_hint.addWidget(QLabel("Yavaş", card))
        speed_hint.addStretch(1)
        speed_hint.addWidget(QLabel("Hızlı", card))
        layout.addLayout(speed_hint)

        return card

    def _build_footer(self, parent: QWidget) -> QVBoxLayout:
        footer = QVBoxLayout()
        footer.setSpacing(8)

        self._progress_bar = QProgressBar(parent)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setVisible(False)
        footer.addWidget(self._progress_bar)

        row = QHBoxLayout()
        row.setSpacing(12)

        self._status_label = QLabel("Hazır", parent)
        self._status_label.setObjectName("StatusLabel")
        row.addWidget(self._status_label, 1, Qt.AlignVCenter)

        self._stop_button = QPushButton(f"Durdur ({HOTKEY_STOP_LABEL})", parent)
        self._stop_button.clicked.connect(self.stop_requested.emit)
        row.addWidget(self._stop_button)

        self._run_button = QPushButton("Çalıştır", parent)
        self._run_button.setObjectName("PrimaryButton")
        self._run_button.clicked.connect(self._emit_run_requested)
        row.addWidget(self._run_button)

        footer.addLayout(row)
        return footer

    # --- Disari acilan API -------------------------------------------------

    def show_normal(self) -> None:
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()
        self._text_edit.setFocus()

    def set_busy(self, busy: bool, status_text: str | None = None) -> None:
        self._run_button.setDisabled(busy)
        self._stop_button.setDisabled(False)
        if status_text is not None:
            self._status_label.setText(status_text)
        else:
            self._status_label.setText("Yazılıyor..." if busy else "Hazır")

    def set_progress(self, done: int, total: int, cps: int) -> None:
        if total <= 0:
            self.clear_progress()
            return

        self._progress_bar.setVisible(True)
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(done)

        remaining_seconds = int((total - done) / max(1, cps))
        self._status_label.setText(f"{done}/{total} karakter · ~{remaining_seconds} sn kaldı")

    def clear_progress(self) -> None:
        self._progress_bar.setVisible(False)
        self._progress_bar.setValue(0)

    def set_speed_value(self, cps: int) -> None:
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(cps)
        self._speed_slider.blockSignals(False)
        self._update_speed_label(cps)

    def speed_value(self) -> int:
        return self._speed_slider.value()

    def prepare_for_exit(self) -> None:
        self._allow_close = True
        self.close()

    # --- Ic isleyis --------------------------------------------------------

    def _emit_run_requested(self) -> None:
        self.run_requested.emit(self._text_edit.toPlainText())

    def _handle_speed_changed(self, value: int) -> None:
        self._update_speed_label(value)
        self.settings_changed.emit()

    def _update_speed_label(self, value: int) -> None:
        self._speed_value_label.setText(f"~{value} karakter/sn")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
            return

        event.ignore()
        self.close_requested.emit()
