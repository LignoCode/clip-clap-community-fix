"""Radar-style live scan display. Blips are positioned by a stable
per-device angle (hashed from address) and distance derived from RSSI --
not a real bearing, just a readable "closer = stronger signal" cue."""

import hashlib
import math

from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget


class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self._devices = {}  # address -> (name, rssi)
        self._sweep_angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_sweep)

    def start_sweep(self):
        self._timer.start(30)

    def stop_sweep(self):
        self._timer.stop()

    def update_device(self, address: str, name: str, rssi: int):
        self._devices[address] = (name, rssi)
        self.update()

    def clear(self):
        self._devices.clear()
        self.update()

    def _advance_sweep(self):
        self._sweep_angle = (self._sweep_angle + 2) % 360
        self.update()

    @staticmethod
    def _angle_for(address: str) -> float:
        h = int(hashlib.md5(address.encode()).hexdigest(), 16)
        return float(h % 360)

    @staticmethod
    def _radius_fraction(rssi: int) -> float:
        """0.0 = strong signal (center), 1.0 = weak signal (edge)."""
        rssi = max(-100, min(-40, rssi))
        return (-40 - rssi) / 60.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 24

        painter.fillRect(self.rect(), QColor("#0a1a12"))

        ring_pen = QPen(QColor("#1d9e75"))
        ring_pen.setWidthF(1)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        for frac in (0.33, 0.66, 1.0):
            r = radius * frac
            painter.drawEllipse(QPointF(cx, cy), r, r)

        rad = math.radians(self._sweep_angle)
        sweep_pen = QPen(QColor(93, 202, 165, 180))
        sweep_pen.setWidthF(2)
        painter.setPen(sweep_pen)
        painter.drawLine(
            QPointF(cx, cy),
            QPointF(cx + radius * math.cos(rad), cy + radius * math.sin(rad)),
        )

        for address, (name, rssi) in self._devices.items():
            angle = self._angle_for(address)
            frac = self._radius_fraction(rssi)
            rad2 = math.radians(angle)
            bx = cx + radius * frac * math.cos(rad2)
            by = cy + radius * frac * math.sin(rad2)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#5dcaa5")))
            painter.drawEllipse(QPointF(bx, by), 6, 6)

            painter.setPen(QColor("#e1f5ee"))
            painter.drawText(QPointF(bx + 10, by + 4), name or address)

        painter.end()
