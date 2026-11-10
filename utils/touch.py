"""Touchscreen and kinetic gesture tracking utility.

Provides robust touch detection, drag-to-scroll tracking, and kinetic momentum
calculation for touchscreen laptops and touch devices.
"""

import math
from typing import List, Optional, Tuple

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QInputDevice, QMouseEvent, QPointingDevice, QSinglePointEvent


def is_touch_event(event: QMouseEvent | QSinglePointEvent) -> bool:
    """Return True if the event originated from a touchscreen, finger, or synthesized touch."""
    try:
        if event.deviceType() == QInputDevice.DeviceType.TouchScreen:
            return True
    except Exception:
        pass

    try:
        p_dev = event.pointingDevice()
        if p_dev is not None:
            if p_dev.type() == QInputDevice.DeviceType.TouchScreen:
                return True
            if p_dev.pointerType() == QPointingDevice.PointerType.Finger:
                return True
    except Exception:
        pass

    return False


class TouchScrollTracker:
    """Tracks touchscreen drag displacements and calculates flick velocities for kinetic momentum."""

    DRAG_THRESHOLD: float = 8.0  # Displacement in px before recognized as intentional scroll

    def __init__(self) -> None:
        self.is_active: bool = False
        self.is_scrolling: bool = False
        self.start_pos: QPointF = QPointF()
        self.last_pos: QPointF = QPointF()
        self.target_region: Optional[Tuple[str, int, float]] = None  # (kind, block_id, max_scroll)
        self._history: List[Tuple[float, float, float]] = []  # (timestamp, dx, dy)

    def start(
        self,
        pos: QPointF,
        timestamp: float,
        target_region: Optional[Tuple[str, int, float]] = None,
    ) -> None:
        """Begin tracking a new touch interaction."""
        self.is_active = True
        self.is_scrolling = False
        self.start_pos = pos
        self.last_pos = pos
        self.target_region = target_region
        self._history = [(timestamp, 0.0, 0.0)]

    def update(self, pos: QPointF, timestamp: float) -> Tuple[float, float, bool]:
        """Process touch movement.

        Returns:
            (dx, dy, is_scrolling): Displacement since last update and whether drag threshold was reached.
        """
        if not self.is_active:
            return (0.0, 0.0, False)

        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        self.last_pos = pos

        self._history.append((timestamp, dx, dy))
        # Keep recent movement history within 150ms window
        self._history = [entry for entry in self._history if timestamp - entry[0] <= 0.15]

        if not self.is_scrolling:
            dist = math.hypot(pos.x() - self.start_pos.x(), pos.y() - self.start_pos.y())
            if dist >= self.DRAG_THRESHOLD:
                self.is_scrolling = True

        return (dx, dy, self.is_scrolling)

    def end(self, timestamp: float) -> Tuple[bool, float, float]:
        """Finish touch interaction.

        Returns:
            (was_scrolling, flick_vx, flick_vy): Whether a scroll occurred and kinetic velocities (px/frame).
        """
        was_scrolling = self.is_scrolling
        vx = 0.0
        vy = 0.0

        if was_scrolling and len(self._history) >= 2:
            self._history = [entry for entry in self._history if timestamp - entry[0] <= 0.15]
            if len(self._history) >= 2:
                dt = self._history[-1][0] - self._history[0][0]
                if dt > 0.01:
                    total_dx = sum(item[1] for item in self._history[1:])
                    total_dy = sum(item[2] for item in self._history[2:]) if len(self._history) > 2 else sum(item[2] for item in self._history[1:])
                    # Velocity normalized to 60 FPS (~16ms/frame)
                    vx = (total_dx / dt) * 0.016
                    vy = (total_dy / dt) * 0.016

        self.reset()
        return (was_scrolling, vx, vy)

    def reset(self) -> None:
        """Reset tracking state to idle."""
        self.is_active = False
        self.is_scrolling = False
        self.target_region = None
        self._history.clear()
