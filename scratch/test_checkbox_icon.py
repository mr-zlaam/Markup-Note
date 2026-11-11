"""Test and render proper checkbox vector icon."""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QPixmap

app = QApplication([])

pixmap = QPixmap(100, 100)
pixmap.fill(QColor("#202022"))

painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

badge_rect = QRect(20, 20, 60, 60)
painter.setBrush(QColor("#28282c"))
painter.setPen(QPen(QColor("#38383e"), 1.5))
painter.drawRoundedRect(badge_rect, 10, 10)

# Draw checkbox inside badge_rect
cx = badge_rect.center().x()
cy = badge_rect.center().y()
box_size = 30.0
half = box_size / 2.0
box_rect = QRectF(cx - half, cy - half, box_size, box_size)

# Rounded box
box_pen = QPen(QColor("#8e8e93"), 2.2)
painter.setPen(box_pen)
painter.setBrush(Qt.BrushStyle.NoBrush)
painter.drawRoundedRect(box_rect, 6.0, 6.0)

# Checkmark
check_pen = QPen(QColor("#0a84ff"), 2.6)
check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
painter.setPen(check_pen)

path = QPainterPath()
path.moveTo(cx - 7.5, cy + 0.5)
path.lineTo(cx - 2.0, cy + 6.0)
path.lineTo(cx + 8.5, cy - 5.5)
painter.drawPath(path)

painter.end()

pixmap.save("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/test_checkbox_vector.png")
print("Saved test_checkbox_vector.png")
