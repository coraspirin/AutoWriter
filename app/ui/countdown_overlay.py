from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CountdownOverlay(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        if hasattr(Qt, "WindowDoesNotAcceptFocus"):
            self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QWidget(self)
        card.setObjectName("CountdownCard")
        layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(6)

        self._title_label = QLabel("Yazma başlayacak", card)
        self._title_label.setObjectName("CountdownTitle")
        self._title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self._title_label)

        self._number_label = QLabel("4", card)
        self._number_label.setObjectName("CountdownNumber")
        self._number_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self._number_label)

    def show_countdown(self, seconds: int) -> None:
        self._title_label.setText("Yazma başlayacak")
        self._number_label.setText(str(seconds))
        self.adjustSize()
        self._move_to_corner()
        self.show()

    def _move_to_corner(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        margin = 28
        x = geometry.right() - self.width() - margin
        y = geometry.bottom() - self.height() - margin
        self.move(x, y)
