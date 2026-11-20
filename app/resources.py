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


def build_refresh_icon(color: str = "#0f766e") -> QIcon:
    """Birbirini takip eden iki yuvarlak ok (guncellemeleri denetle). Yuksek DPI
    ekranlarda net gorunsun diye 64 px cizilir; buton bunu kucuk boyutta gosterir."""
    import math

    size = 64
    center = QPointF(size / 2, size / 2)
    radius = 19.0
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidthF(6.0)
    pen.setCapStyle(Qt.FlatCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    circle = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
    # Iki yay; aralarinda bosluk birakilir, her yayin sonunda ok basi olur.
    # Qt acilari: 0 = saat 3 yonu, saat yonunun tersine artar.
    arcs = ((40.0, 125.0), (220.0, 125.0))
    for start, span in arcs:
        path = QPainterPath()
        path.arcMoveTo(circle, start)
        path.arcTo(circle, start, span)
        painter.drawPath(path)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    for start, span in arcs:
        theta = math.radians(start + span)
        point = QPointF(center.x() + radius * math.cos(theta), center.y() - radius * math.sin(theta))
        direction = QPointF(-math.sin(theta), -math.cos(theta))  # yay yonunde teget
        normal = QPointF(math.cos(theta), -math.sin(theta))  # disa dogru
        tip = point + direction * 11
        base_back = point - direction * 2
        arrow = QPainterPath()
        arrow.moveTo(tip)
        arrow.lineTo(base_back + normal * 9)
        arrow.lineTo(base_back - normal * 9)
        arrow.closeSubpath()
        painter.drawPath(arrow)

    painter.end()
    return QIcon(pixmap)
