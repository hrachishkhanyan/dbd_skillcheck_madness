import math
import os
import sys
import time
import ctypes
from enum import Enum, auto

from PySide6.QtCore import Qt, QTimer, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QPixmap,
    QRadialGradient,
    QFontMetrics,
)
from PySide6.QtWidgets import QWidget, QApplication

from config import (
    RING_RADIUS,
    RING_WIDTH,
    ANIMATION_INTERVAL,
    RESULT_DISPLAY_MS,
    FAIL_ANIMATION_MS,
    WARNING_DURATION_MS,
    SKILL_CHECK_TIMEOUT_BUFFER,
    JUMPSCARE_DISPLAY_MS,
)


class _State(Enum):
    HIDDEN = auto()
    WARNING = auto()
    ACTIVE = auto()
    RESULT = auto()
    JUMPSCARE = auto()


class SkillCheckOverlay(QWidget):
    """Full-screen transparent overlay that renders the skill-check dial."""

    check_completed = Signal(str, float)  # result, reaction_time_ms

    # ── Visual constants ──
    _CLR_RING = QColor(200, 200, 210, 100)      # thin base ring
    _CLR_GOOD = QColor(255, 255, 255, 200)       # good zone arc
    _CLR_GREAT = QColor(255, 255, 255, 255)      # great zone arc (brightest)
    _CLR_POINTER = QColor(220, 40, 40, 255)      # red needle
    _CLR_BG = QColor(10, 10, 20, 140)            # background glow
    _CLR_RESULT_FAIL = QColor(220, 50, 50)       # fail red tint target
    _RING_W = 3                                   # base ring line width
    _ZONE_W = 10                                  # zone arc line width
    _POINTER_W = 3                                # pointer line width

    def __init__(self, sound_manager=None, parent=None):
        super().__init__(parent)
        self._sounds = sound_manager
        self.hotkey_label: str = "SPACE"
        self.jumpscare_enabled: bool = False

        # Load jumpscare image
        _base = os.path.join(sys._MEIPASS, "overlay") if getattr(sys, '_MEIPASS', None) else os.path.dirname(os.path.abspath(__file__))
        _img_path = os.path.join(_base, "jumpscare.png")
        self._jumpscare_pixmap = QPixmap(_img_path) if os.path.isfile(_img_path) else None
        # Window behaviour – frameless, topmost, no taskbar entry
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Span the entire primary screen
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        # Internal state
        self._state = _State.HIDDEN
        self._config = None
        self._pointer_angle = 0.0
        self._start_time = 0.0
        self._last_frame = 0.0
        self._current_speed = 0.0
        self._current_clockwise = True
        self._pending_result = ""
        self._pending_reaction = 0.0
        self._fail_progress = 0.0
        self._fail_start_time = 0.0

        # ---- Timers ----
        self._anim_timer = QTimer(self)
        self._anim_timer.setTimerType(Qt.PreciseTimer)
        self._anim_timer.timeout.connect(self._on_frame)

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

        self._result_timer = QTimer(self)
        self._result_timer.setSingleShot(True)
        self._result_timer.timeout.connect(self._on_result_done)

        self._jumpscare_timer = QTimer(self)
        self._jumpscare_timer.setSingleShot(True)
        self._jumpscare_timer.timeout.connect(self._on_jumpscare_done)

        self._warning_timer = QTimer(self)
        self._warning_timer.setSingleShot(True)
        self._warning_timer.timeout.connect(self._start_active)

    # ==================================================================
    # Win32 helpers
    # ==================================================================
    def _make_click_through(self):
        """Add WS_EX_TRANSPARENT so clicks pass through to windows below."""
        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT
            )
        except Exception:
            pass

    def _force_topmost(self):
        """Force HWND_TOPMOST via Win32 to stay above borderless-fullscreen apps."""
        try:
            hwnd = int(self.winId())
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            HWND_TOPMOST = -1
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    # ==================================================================
    # Public API
    # ==================================================================
    def start_check(self, config):
        """Begin a new skill check with the given config."""
        self._stop_all_timers()
        self._config = config

        # Storm continuation: ring already visible, skip warning & cue
        if config.storm and self.isVisible():
            self._start_active()
            return

        self._state = _State.WARNING

        # Re-span screen (handle resolution changes)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self.show()
        self._make_click_through()
        self._force_topmost()

        # Audible cue
        if self._sounds:
            self._sounds.play_cue()

        # Synchronous repaint so the stale backing-store is never visible
        self.repaint()
        self._warning_timer.start(WARNING_DURATION_MS)

    def on_key_pressed(self):
        """Called by the global listener when the hotkey is hit."""
        if self._state != _State.ACTIVE:
            return

        self._anim_timer.stop()
        self._timeout_timer.stop()

        reaction_ms = (time.perf_counter() - self._start_time) * 1000
        result = self._calc_result()
        self._show_result(result, reaction_ms)

    def cancel(self):
        """Immediately dismiss any active skill check."""
        self._stop_all_timers()
        self._state = _State.HIDDEN
        self.repaint()   # clear backing store
        self.hide()

    # ==================================================================
    # Internal flow
    # ==================================================================
    def _start_active(self):
        self._state = _State.ACTIVE
        self._pointer_angle = self._config.pointer_start
        self._current_speed = self._config.pointer_speed
        self._current_clockwise = self._config.clockwise
        self._start_time = time.perf_counter()
        self._last_frame = self._start_time

        timeout_ms = int((360.0 / self._config.pointer_speed) * 1000) + SKILL_CHECK_TIMEOUT_BUFFER
        self._timeout_timer.start(timeout_ms)
        self._anim_timer.start(ANIMATION_INTERVAL)

    def _on_timeout(self):
        if self._state != _State.ACTIVE:
            return
        self._anim_timer.stop()
        reaction_ms = (time.perf_counter() - self._start_time) * 1000
        self._show_result("miss", reaction_ms)

    def _show_result(self, result: str, reaction_ms: float):
        self._state = _State.RESULT
        self._pending_result = result
        self._pending_reaction = reaction_ms

        if self._sounds:
            self._sounds.play_result(result)

        is_fail = result in ("fail", "miss")
        if is_fail:
            # Start gradual red animation
            self._fail_progress = 0.0
            self._fail_start_time = time.perf_counter()
            self._anim_timer.start(ANIMATION_INTERVAL)
            display_ms = 150 if (self._config and self._config.storm) else FAIL_ANIMATION_MS
        else:
            display_ms = 150 if (self._config and self._config.storm) else RESULT_DISPLAY_MS

        self.update()
        self._result_timer.start(display_ms)

    def _on_result_done(self):
        self._anim_timer.stop()
        result = self._pending_result
        reaction = self._pending_reaction
        is_storm = self._config and self._config.storm

        # Trigger jumpscare on fail/miss if enabled
        if (self.jumpscare_enabled
                and result in ("fail", "miss")
                and not is_storm
                and self._jumpscare_pixmap):
            self._state = _State.JUMPSCARE
            if self._sounds:
                self._sounds.play_jumpscare()
            self.repaint()
            self._jumpscare_timer.start(JUMPSCARE_DISPLAY_MS)
            return

        if not is_storm:
            self._state = _State.HIDDEN
            self.repaint()   # clear backing store to transparent before hiding
            self.hide()
        self.check_completed.emit(result, reaction)

    def _on_jumpscare_done(self):
        result = self._pending_result
        reaction = self._pending_reaction
        self._state = _State.HIDDEN
        self.repaint()   # clear backing store
        self.hide()
        self.check_completed.emit(result, reaction)

    # ==================================================================
    # Animation
    # ==================================================================
    def _on_frame(self):
        now = time.perf_counter()
        dt = now - self._last_frame
        self._last_frame = now

        if self._state == _State.RESULT and self._pending_result in ("fail", "miss"):
            # Update fail-red progress (0 -> 1)
            elapsed = (now - self._fail_start_time) * 1000
            duration = 150 if (self._config and self._config.storm) else FAIL_ANIMATION_MS
            self._fail_progress = min(elapsed / duration, 1.0)
        else:
            direction = 1.0 if self._current_clockwise else -1.0
            self._pointer_angle += self._current_speed * dt * direction
            self._pointer_angle %= 360

        self.update()

    # ==================================================================
    # Result calculation
    # ==================================================================
    def _calc_result(self) -> str:
        angle = self._pointer_angle % 360
        zone_start = self._config.zone_start % 360
        good_size = self._config.good_zone_size
        great_size = self._config.great_zone_size

        if great_size <= 0:
            # Storm mode — no great zone
            if self._in_arc(angle, zone_start, good_size):
                return "good"
            return "fail"

        if self._config.reverse:
            # Reverse: great zone at the START of the good zone
            great_start = zone_start
        else:
            # Normal: great zone at the END of the good zone
            great_start = (zone_start + good_size - great_size) % 360

        if self._in_arc(angle, great_start, great_size):
            return "great"
        if self._in_arc(angle, zone_start, good_size):
            return "good"
        return "fail"

    @staticmethod
    def _in_arc(angle: float, start: float, size: float) -> bool:
        """Check if *angle* lies within an arc starting at *start* spanning *size* degrees CW."""
        angle %= 360
        start %= 360
        end = (start + size) % 360
        if start <= end:
            return start <= angle <= end
        return angle >= start or angle <= end

    # ==================================================================
    # Painting
    # ==================================================================
    def paintEvent(self, event):  # noqa: N802
        if self._state == _State.HIDDEN:
            return

        # -- Jumpscare fullscreen image --
        if self._state == _State.JUMPSCARE and self._jumpscare_pixmap:
            painter = QPainter(self)
            scaled = self._jumpscare_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        screen = QApplication.primaryScreen()
        sw = screen.geometry().width() if screen else self.width()
        sh = screen.geometry().height() if screen else self.height()

        cx = sw / 2 + (self._config.offset_x if self._config else 0)
        cy = sh / 2 + (self._config.offset_y if self._config else 0)

        radius = RING_RADIUS

        # -- WARNING flash --
        if self._state == _State.WARNING:
            grad = QRadialGradient(cx, cy, radius + 60)
            grad.setColorAt(0, QColor(255, 255, 255, 50))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), radius + 60, radius + 60)
            painter.end()
            return

        # -- Background glow --
        grad = QRadialGradient(cx, cy, radius + 80)
        grad.setColorAt(0, self._CLR_BG)
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius + 80, radius + 80)

        # -- Determine if we're in a fail animation --
        _is_fail_anim = (
            self._state == _State.RESULT
            and self._pending_result in ("fail", "miss")
        )
        _fp = self._fail_progress if _is_fail_anim else 0.0

        # -- Base ring (thin circle) --
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        ring_clr = self._lerp_color(self._CLR_RING, self._CLR_RESULT_FAIL, _fp)
        pen = QPen(ring_clr, self._RING_W, Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        if self._config and self._state in (_State.ACTIVE, _State.RESULT):
            zone_start = self._config.zone_start
            good_size = self._config.good_zone_size
            great_size = self._config.great_zone_size

            # Convert angle system:
            #   Mine:  0° = 12 o'clock, CW positive
            #   Qt  :  0° = 3 o'clock,  CCW positive, units of 1/16°
            qt_good_start = (90 - zone_start) * 16
            qt_good_span = -good_size * 16

            # Great zone: at START for reverse, at END for normal
            if self._config.reverse:
                great_start_angle = zone_start
            else:
                great_start_angle = zone_start + good_size - great_size
            qt_great_start = (90 - great_start_angle) * 16
            qt_great_span = -great_size * 16

            # -- Good zone arc (thicker, brighter) --
            good_clr = self._lerp_color(self._CLR_GOOD, self._CLR_RESULT_FAIL, _fp)
            pen = QPen(good_clr, self._ZONE_W, Qt.SolidLine, Qt.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, int(qt_good_start), int(qt_good_span))

            # -- Great zone arc (brightest, slightly thicker) --
            if great_size > 0:
                great_clr = self._lerp_color(self._CLR_GREAT, self._CLR_RESULT_FAIL, _fp)
                pen = QPen(great_clr, self._ZONE_W + 2, Qt.SolidLine, Qt.FlatCap)
                painter.setPen(pen)
                painter.drawArc(rect, int(qt_great_start), int(qt_great_span))

            # -- Zone boundary marker (small notch at end of good zone) --
            end_angle = zone_start + good_size
            end_rad = math.radians(end_angle)
            mx = cx + radius * math.sin(end_rad)
            my = cy - radius * math.cos(end_rad)
            notch_clr = self._lerp_color(QColor(255, 255, 255, 220), self._CLR_RESULT_FAIL, _fp)
            painter.setBrush(QBrush(notch_clr))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(mx, my), 5, 5)

            # -- Pointer (red needle) --
            angle_rad = math.radians(self._pointer_angle)
            sin_a = math.sin(angle_rad)
            cos_a = math.cos(angle_rad)

            inner_r = radius - self._ZONE_W
            outer_r = radius + self._ZONE_W
            ix = cx + inner_r * sin_a
            iy = cy - inner_r * cos_a
            ox = cx + outer_r * sin_a
            oy = cy - outer_r * cos_a

            pen = QPen(self._CLR_POINTER, self._POINTER_W, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(ix, iy), QPointF(ox, oy))

        # -- Hotkey label (center pill) --
        self._draw_hotkey_label(painter, cx, cy)

        painter.end()

    def _draw_hotkey_label(self, painter: QPainter, cx: float, cy: float):
        """Draw the hotkey name inside a rounded dark rectangle at the center."""
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text = self.hotkey_label
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        pad_x, pad_y = 18, 8
        rw = tw + pad_x * 2
        rh = th + pad_y * 2
        rx = cx - rw / 2
        ry = cy - rh / 2

        rect = QRectF(rx, ry, rw, rh)

        # Dark fill
        painter.setBrush(QBrush(QColor(15, 15, 25, 230)))
        painter.setPen(QPen(QColor(200, 200, 210, 180), 2))
        painter.drawRoundedRect(rect, 8, 8)

        # Text
        painter.setPen(QColor(220, 220, 230))
        painter.drawText(rect, Qt.AlignCenter, text)

    # ==================================================================
    # Helpers
    # ==================================================================
    @staticmethod
    def _lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
        """Linearly interpolate between two QColors by factor *t* (0..1)."""
        return QColor(
            int(c1.red()   + (c2.red()   - c1.red())   * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue()  + (c2.blue()  - c1.blue())  * t),
            int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
        )

    def _stop_all_timers(self):
        self._anim_timer.stop()
        self._timeout_timer.stop()
        self._result_timer.stop()
        self._jumpscare_timer.stop()
        self._warning_timer.stop()
