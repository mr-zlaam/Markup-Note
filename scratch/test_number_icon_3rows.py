"""Refine number list vector icon with 3 rows."""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPixmap

app = QApplication([])

pix = QPixmap(60, 60)
pix.fill(QColor("#202024"))
p = QPainter(pix)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.scale(4.0, 4.0)

num_font = QFont("Cantarell", 3)
num_font.setBold(True)
p.setFont(num_font)
p.setPen(QColor("#d0d0d4"))

rows = [("1", 3.5), ("2", 7.0), ("3", 10.5)]
pen = QPen(QColor("#d0d0d4"), 1.2)
pen.setCapStyle(Qt.PenCapStyle.RoundCap)

for num, y in rows:
    p.drawText(QRectF(0.5, y - 2.2, 3.5, 4.0), Qt.AlignmentFlag.AlignCenter, num)
    p.setPen(pen)
    p.drawLine(QPointF(5.5, y), QPointF(12.0, y))
    p.setPen(QColor("#d0d0d4"))

p.end()
pix.save("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/test_number_icon_3rows.png")
print("Saved test_number_icon_3rows.png")
