# powered by mucahid erdogan
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
    APP_VERSION,
    HOTKEY_STOP_LABEL,
    TAB_WIDTH_CHOICES,
    TARGET_LAYOUTS,
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
    update_requested = Signal()

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

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addLayout(self._build_brand(root_panel))
        header.addStretch(1)

        # Sag ust: yalnizca yeni surum bulununca gorunur.
        self._update_button = QPushButton("", root_panel)
        self._update_button.setObjectName("UpdateButton")
        self._update_button.setCursor(Qt.PointingHandCursor)
        self._update_button.setVisible(False)
        self._update_button.clicked.connect(self.update_requested.emit)
        header.addWidget(self._update_button, 0, Qt.AlignTop)

        panel_layout.addLayout(header)

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

        brand_subtitle = QLabel(f"Auto Writer  v{APP_VERSION}", parent)
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

        self._indent_checkbox = QCheckBox("Kod girintisini temizle", card)
        self._indent_checkbox.setToolTip(
            "Kod editörlerinin Enter sonrası eklediği otomatik girintiyi siler "
            "(her satırda Shift+Home, Delete).\n"
            "Düz metin yazarken kapatmak satır başına zaman kazandırır."
        )
        self._indent_checkbox.toggled.connect(lambda _checked: self.settings_changed.emit())
        layout.addWidget(self._indent_checkbox)

        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(0, 0, 0, 0)
        tab_row.setSpacing(8)
        self._expand_tabs_checkbox = QCheckBox("Tab'ları boşluğa çevir", card)
        self._expand_tabs_checkbox.setToolTip(
            "Metindeki Tab karakterlerini yazmadan önce boşluğa çevirir.\n"
            "Kod editörlerinde Tab otomatik tamamlamayı tetikleyebilir; boşluk birebir yazılır."
        )
        self._expand_tabs_checkbox.toggled.connect(self._handle_expand_tabs_toggled)
        tab_row.addWidget(self._expand_tabs_checkbox)
        self._tab_width_combo = QComboBox(card)
        for width in TAB_WIDTH_CHOICES:
            self._tab_width_combo.addItem(f"{width} boşluk", width)
        self._tab_width_combo.currentIndexChanged.connect(lambda _i: self.settings_changed.emit())
        tab_row.addWidget(self._tab_width_combo)
        tab_row.addStretch(1)
        layout.addLayout(tab_row)

        layout_row = QHBoxLayout()
        layout_row.setContentsMargins(0, 0, 0, 0)
        layout_row.setSpacing(8)
        layout_label = QLabel("Hedef klavye:", card)
        layout_label.setObjectName("FieldLabel")
        layout_row.addWidget(layout_label)
        self._layout_combo = QComboBox(card)
        for key, (label, _klid) in TARGET_LAYOUTS.items():
            self._layout_combo.addItem(label, key)
        self._layout_combo.setToolTip(
            "Yazılan makinenin (ör. RDP'deki uzak bilgisayarın) klavye düzeni.\n"
            "Uzak makinenin düzeni bu bilgisayardan farklıysa seçin; aksi halde "
            "Türkçe harfler ve semboller yanlış çıkar."
        )
        self._layout_combo.currentIndexChanged.connect(lambda _i: self.settings_changed.emit())
        layout_row.addWidget(self._layout_combo)
        layout_row.addStretch(1)
        layout.addLayout(layout_row)

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

    def set_target_layout(self, key: str) -> None:
        index = self._layout_combo.findData(key)
        self._layout_combo.blockSignals(True)
        self._layout_combo.setCurrentIndex(max(0, index))
        self._layout_combo.blockSignals(False)

    def target_layout(self) -> str:
        return str(self._layout_combo.currentData())

    def set_expand_tabs(self, enabled: bool, width: int) -> None:
        self._expand_tabs_checkbox.blockSignals(True)
        self._expand_tabs_checkbox.setChecked(enabled)
        self._expand_tabs_checkbox.blockSignals(False)
        index = self._tab_width_combo.findData(width)
        self._tab_width_combo.blockSignals(True)
        self._tab_width_combo.setCurrentIndex(max(0, index))
        self._tab_width_combo.blockSignals(False)
        self._tab_width_combo.setEnabled(enabled)

    def expand_tabs(self) -> bool:
        return self._expand_tabs_checkbox.isChecked()

    def tab_width(self) -> int:
        return int(self._tab_width_combo.currentData())

    def set_clear_auto_indent(self, enabled: bool) -> None:
        self._indent_checkbox.blockSignals(True)
        self._indent_checkbox.setChecked(enabled)
        self._indent_checkbox.blockSignals(False)

    def clear_auto_indent(self) -> bool:
        return self._indent_checkbox.isChecked()

    def show_update_available(self, version: str) -> None:
        self._update_button.setText(f"⬇  Güncelle  v{version}")
        self._update_button.setToolTip(
            f"Yeni sürüm hazır: v{version} (şu an v{APP_VERSION}). İndirip kurmak için tıklayın."
        )
        self._update_button.setEnabled(True)
        self._update_button.setVisible(True)

    def set_update_state(self, text: str, enabled: bool) -> None:
        self._update_button.setText(text)
        self._update_button.setEnabled(enabled)
        self._update_button.setVisible(True)

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def prepare_for_exit(self) -> None:
        self._allow_close = True
        self.close()

    # --- Ic isleyis --------------------------------------------------------

    def _emit_run_requested(self) -> None:
        self.run_requested.emit(self._text_edit.toPlainText())

    def _handle_expand_tabs_toggled(self, checked: bool) -> None:
        self._tab_width_combo.setEnabled(checked)
        self.settings_changed.emit()

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
