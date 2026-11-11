"""Test bullet and number list vector icons."""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPixmap

app = QApplication([])

def test_icons():
    # Bullet icon
    pix1 = QPixmap(60, 60)
    pix1.fill(QColor("#202024"))
    p1 = QPainter(pix1)
    p1.setRenderHint(QPainter.RenderHint.Antialiasing)
    p1.scale(4.0, 4.0)

    p1.setPen(Qt.PenStyle.NoPen)
    p1.setBrush(QColor("#d0d0d4"))
    r = 1.1
    for y in (3.5, 7.0, 10.5):
        p1.drawEllipse(QPointF(2.5, y), r, r)

    pen = QPen(QColor("#d0d0d4"), 1.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p1.setPen(pen)
    for y in (3.5, 7.0, 10.5):
        p1.drawLine(QPointF(5.5, y), QPointF(12.0, y))
    p1.end()
    pix1.save("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/test_bullet_icon.png")

    # Number icon
    pix2 = QPixmap(60, 60)
    pix2.fill(QColor("#202024"))
    p2 = QPainter(pix2)
    p2.setRenderHint(QPainter.RenderHint.Antialiasing)
    p2.scale(4.0, 4.0)

    num_font = QFont("Cantarell", 5)
    num_font.setBold(True)
    p2.setFont(num_font)
    p2.setPen(QColor("#d0d0d4"))
    p2.drawText(QRectF(0.5, 0.8, 4.5, 5.5), Qt.AlignmentFlag.AlignCenter, "1")
    p2.drawText(QRectF(0.5, 7.2, 4.5, 5.5), Qt.AlignmentFlag.AlignCenter, "2")

    pen2 = QPen(QColor("#d0d0d4"), 1.2)
    pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p2.setPen(pen2)
    p2.drawLine(QPointF(6.0, 3.8), QPointF(12.0, 3.8))
    p2.drawLine(QPointF(6.0, 10.2), QPointF(12.0, 10.2))
    p2.end()
    pix2.save("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/test_number_icon.png")
    print("Icons saved successfully!")

test_icons()
