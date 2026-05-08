from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap


def build_app_icon() -> QIcon:
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    background_gradient = QLinearGradient(0, 0, size, size)
    background_gradient.setColorAt(0.0, QColor("#0f766e"))
    background_gradient.setColorAt(1.0, QColor("#155e75"))

    painter.setPen(Qt.NoPen)
    painter.setBrush(background_gradient)
    painter.drawRoundedRect(QRectF(4, 4, 56, 56), 16, 16)

    paper = QPainterPath()
    paper.moveTo(19, 14)
    paper.lineTo(41, 14)
    paper.lineTo(47, 20)
    paper.lineTo(47, 47)
    paper.lineTo(19, 47)
    paper.closeSubpath()
    painter.setBrush(QColor("#f8fafc"))
    painter.drawPath(paper)

    fold = QPainterPath()
    fold.moveTo(41, 14)
    fold.lineTo(41, 20)
    fold.lineTo(47, 20)
    painter.setBrush(QColor("#cbd5e1"))
    painter.drawPath(fold)

    pen = QPen(QColor("#0f172a"))
    pen.setWidthF(2.0)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(24, 27), QPointF(42, 27))
    painter.drawLine(QPointF(24, 33), QPointF(42, 33))
    painter.drawLine(QPointF(24, 39), QPointF(37, 39))

    accent_pen = QPen(QColor("#f97316"))
    accent_pen.setWidthF(4.0)
    accent_pen.setCapStyle(Qt.RoundCap)
    painter.setPen(accent_pen)
    painter.drawLine(QPointF(15, 45), QPointF(24, 36))

    painter.end()
    return QIcon(pixmap)
