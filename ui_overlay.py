import os
import sys
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QBrush
from PySide6.QtWidgets import QApplication, QWidget


if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")


class Overlay(QWidget):
    def __init__(self, level_getter):
        super().__init__()
        self.level_getter = level_getter
        self.current = 0.0
        self.target = 0.0

        self.setFixedSize(76, 32)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.bottom() - 105
        self.move(x, y)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

        self.show()

    def animate(self):
        self.target = float(self.level_getter())
        factor = 0.35 if self.target > self.current else 0.16
        self.current += (self.target - self.current) * factor
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        p.setBrush(QBrush(Qt.black))
        p.drawRoundedRect(
            0, 0, self.width(), self.height(), 16, 16
        )

        level = self.current
        base = np.array([8, 13, 18, 13, 8], dtype=float)
        mult = np.array([0.75, 0.95, 1.15, 0.95, 0.75])
        heights = np.clip(
            base * (0.28 + level * mult),
            5,
            25,
        ).astype(int)

        bw = 5
        gap = 4
        total = 5 * bw + 4 * gap
        start = (self.width() - total) // 2
        cy = self.height() // 2

        p.setBrush(QBrush(Qt.white))

        for i, h in enumerate(heights):
            x = start + i * (bw + gap)
            y = cy - h // 2
            p.drawRoundedRect(
                x, y, bw, h, bw / 2, bw / 2
            )

        p.end()


def create_app():
    return QApplication.instance() or QApplication(sys.argv)
