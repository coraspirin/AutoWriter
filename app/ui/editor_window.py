from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    TYPE_SPEED_SLIDER_MAX,
    TYPE_SPEED_SLIDER_MIN,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)


class EditorWindow(QWidget):
    run_requested = Signal(str)
    speed_changed = Signal(int)
    close_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self._build_ui()

    @property
    def text_edit(self) -> QTextEdit:
        return self._text_edit

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

        self._text_edit = QTextEdit(root_panel)
        self._text_edit.setPlaceholderText(
            "Yazdırılacak metni buraya girin. Satırlar ve özel karakterler korunur."
        )
        panel_layout.addWidget(self._text_edit, 1)

        speed_card = QFrame(root_panel)
        speed_card.setObjectName("SpeedCard")
        speed_layout = QVBoxLayout(speed_card)
        speed_layout.setContentsMargins(16, 14, 16, 14)
        speed_layout.setSpacing(8)

        speed_header = QHBoxLayout()
        speed_header.setContentsMargins(0, 0, 0, 0)

        speed_title = QLabel("Yazma Hızı", speed_card)
        speed_title.setObjectName("SectionLabel")
        speed_header.addWidget(speed_title)

        self._speed_value_label = QLabel("", speed_card)
        self._speed_value_label.setObjectName("SpeedValueLabel")
        speed_header.addWidget(self._speed_value_label, 0, Qt.AlignRight)

        speed_layout.addLayout(speed_header)

        self._speed_slider = QSlider(Qt.Horizontal, speed_card)
        self._speed_slider.setRange(TYPE_SPEED_SLIDER_MIN, TYPE_SPEED_SLIDER_MAX)
        self._speed_slider.setSingleStep(1)
        self._speed_slider.setPageStep(2)
        self._speed_slider.valueChanged.connect(self._handle_speed_changed)
        speed_layout.addWidget(self._speed_slider)

        speed_hint_layout = QHBoxLayout()
        speed_hint_layout.setContentsMargins(0, 0, 0, 0)
        speed_hint_layout.addWidget(QLabel("Hızlı", speed_card))
        speed_hint_layout.addStretch(1)
        speed_hint_layout.addWidget(QLabel("Yavaş", speed_card))
        speed_layout.addLayout(speed_hint_layout)

        panel_layout.addWidget(speed_card)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)

        self._status_label = QLabel("Hazır", root_panel)
        self._status_label.setObjectName("StatusLabel")
        footer_layout.addWidget(self._status_label, 1, Qt.AlignVCenter)

        self._close_button = QPushButton("Kapat", root_panel)
        self._close_button.clicked.connect(self.close)
        footer_layout.addWidget(self._close_button)

        self._run_button = QPushButton("Çalıştır", root_panel)
        self._run_button.setObjectName("PrimaryButton")
        self._run_button.clicked.connect(self._emit_run_requested)
        footer_layout.addWidget(self._run_button)

        panel_layout.addLayout(footer_layout)
        self.set_speed_value(10)

    def show_normal(self) -> None:
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()
        self._text_edit.setFocus()

    def set_busy(self, busy: bool, status_text: str | None = None) -> None:
        self._run_button.setDisabled(busy)
        self._speed_slider.setDisabled(busy)
        self._close_button.setDisabled(False)
        if status_text is not None:
            self._status_label.setText(status_text)
            return

        self._status_label.setText("Yazılıyor..." if busy else "Hazır")

    def set_speed_value(self, value: int) -> None:
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(value)
        self._speed_slider.blockSignals(False)
        self._update_speed_label(value)

    def prepare_for_exit(self) -> None:
        self._allow_close = True
        self.close()

    def _emit_run_requested(self) -> None:
        self.run_requested.emit(self._text_edit.toPlainText())

    def _handle_speed_changed(self, value: int) -> None:
        self._update_speed_label(value)
        self.speed_changed.emit(value)

    def _update_speed_label(self, value: int) -> None:
        self._speed_value_label.setText(f"{value}/{TYPE_SPEED_SLIDER_MAX}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
            return

        event.ignore()
        self.close_requested.emit()
