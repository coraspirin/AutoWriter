# powered by mucahid erdogan
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
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
    TARGET_LAYOUTS,
    TYPE_CPS_MAX,
    TYPE_CPS_MIN,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)
from app.resources import build_refresh_icon


class EditorWindow(QWidget):
    run_requested = Signal(str)
    stop_requested = Signal()
    close_requested = Signal()
    settings_changed = Signal()
    update_requested = Signal()
    check_updates_requested = Signal()

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

        # Sag ust: [durum yazisi] [Guncelle (yeni surum varsa)] [denetle ikonu]
        update_row = QHBoxLayout()
        update_row.setContentsMargins(0, 0, 0, 0)
        update_row.setSpacing(8)

        self._update_status_label = QLabel("", root_panel)
        self._update_status_label.setObjectName("UpdateStatusLabel")
        self._update_status_label.setVisible(False)
        update_row.addWidget(self._update_status_label, 0, Qt.AlignVCenter)

        self._update_button = QPushButton("", root_panel)
        self._update_button.setObjectName("UpdateButton")
        self._update_button.setCursor(Qt.PointingHandCursor)
        self._update_button.setVisible(False)
        self._update_button.clicked.connect(self.update_requested.emit)
        update_row.addWidget(self._update_button, 0, Qt.AlignVCenter)

        self._check_button = QPushButton("", root_panel)
        self._check_button.setObjectName("IconButton")
        self._check_button.setIcon(build_refresh_icon())
        self._check_button.setIconSize(QSize(18, 18))
        self._check_button.setFixedSize(34, 34)
        self._check_button.setCursor(Qt.PointingHandCursor)
        self._check_button.setToolTip("Güncellemeleri denetle")
        self._check_button.clicked.connect(self.check_updates_requested.emit)
        update_row.addWidget(self._check_button, 0, Qt.AlignVCenter)

        header.addLayout(update_row)
        header.setAlignment(update_row, Qt.AlignTop)

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
        speed_header.addStretch(1)

        self._speed_value_label = QLabel("", card)
        self._speed_value_label.setObjectName("SpeedValueLabel")
        speed_header.addWidget(self._speed_value_label)

        layout.addLayout(speed_header)

        self._speed_slider = QSlider(Qt.Horizontal, card)
        self._speed_slider.setRange(TYPE_CPS_MIN, TYPE_CPS_MAX)
        self._speed_slider.setSingleStep(1)
        self._speed_slider.setPageStep(5)
        self._speed_slider.valueChanged.connect(self._handle_speed_changed)
        layout.addWidget(self._speed_slider)

        speed_hint = QHBoxLayout()
        speed_hint.setContentsMargins(0, 0, 0, 0)
        slow_label = QLabel("Yavaş", card)
        slow_label.setObjectName("HintLabel")
        fast_label = QLabel("Hızlı", card)
        fast_label.setObjectName("HintLabel")
        speed_hint.addWidget(slow_label)
        speed_hint.addStretch(1)
        speed_hint.addWidget(fast_label)
        layout.addLayout(speed_hint)

        divider = QFrame(card)
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        layout.addSpacing(2)
        layout.addWidget(divider)
        layout.addSpacing(2)

        # Ayarlar tek satirda: solda girinti secimi, sagda hedef klavye.
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(0, 0, 0, 0)
        settings_row.setSpacing(10)

        self._indent_checkbox = QCheckBox("Kod girintisini temizle", card)
        self._indent_checkbox.setToolTip(
            "Kod editörlerinin Enter sonrası eklediği otomatik girintiyi siler "
            "(her satırda Shift+Home, Delete).\n"
            "Düz metin yazarken kapatmak satır başına zaman kazandırır."
        )
        self._indent_checkbox.toggled.connect(lambda _checked: self.settings_changed.emit())
        settings_row.addWidget(self._indent_checkbox)
        settings_row.addStretch(1)

        layout_label = QLabel("Hedef klavye", card)
        layout_label.setObjectName("FieldLabel")
        settings_row.addWidget(layout_label)
        self._layout_combo = QComboBox(card)
        for key, (label, _klid) in TARGET_LAYOUTS.items():
            self._layout_combo.addItem(label, key)
        self._layout_combo.setToolTip(
            "Yazılan makinenin (ör. RDP'deki uzak bilgisayarın) klavye düzeni.\n"
            "Otomatik: bu bilgisayarın düzeni. TR-Q: Türkçe Q. US-US: İngilizce (ABD).\n"
            "Uzak makinenin düzeni bu bilgisayardan farklıysa seçin; aksi halde "
            "Türkçe harfler ve semboller yanlış çıkar."
        )
        self._layout_combo.currentIndexChanged.connect(lambda _i: self.settings_changed.emit())
        self._layout_combo.setFixedWidth(130)
        settings_row.addWidget(self._layout_combo)

        layout.addLayout(settings_row)

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

    def set_clear_auto_indent(self, enabled: bool) -> None:
        self._indent_checkbox.blockSignals(True)
        self._indent_checkbox.setChecked(enabled)
        self._indent_checkbox.blockSignals(False)

    def clear_auto_indent(self) -> bool:
        return self._indent_checkbox.isChecked()

    def set_update_check_state(self, state: str) -> None:
        """state: checking | up_to_date | failed. Yeni surum durumu icin
        show_update_available kullanilir."""
        texts = {
            "checking": "Denetleniyor…",
            "up_to_date": "✓ Güncel",
            "failed": "Denetlenemedi",
        }
        self._update_status_label.setText(texts.get(state, ""))
        self._update_status_label.setProperty("state", state)
        # Dinamik ozellik degisince QSS yeniden uygulansin (renk duruma gore).
        self._update_status_label.style().unpolish(self._update_status_label)
        self._update_status_label.style().polish(self._update_status_label)
        self._update_status_label.setVisible(state in texts)
        self._update_status_label.setToolTip(
            f"Bu sürüm (v{APP_VERSION}) en günceli." if state == "up_to_date" else ""
        )
        self._check_button.setEnabled(state != "checking")
        if state != "checking":
            self._update_button.setVisible(False)

    def show_update_available(self, version: str) -> None:
        self._update_status_label.setVisible(False)
        self._check_button.setEnabled(True)
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
