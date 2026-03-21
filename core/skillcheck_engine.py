import random

from PySide6.QtCore import QObject, Signal, QTimer

from config import (
    DEFAULT_POINTER_SPEED,
    DEFAULT_GOOD_ZONE_SIZE,
    DEFAULT_GREAT_ZONE_SIZE,
    DEFAULT_MIN_INTERVAL,
    DEFAULT_MAX_INTERVAL,
    STORM_DURATION_MS,
    STORM_DELAY_MS,
    STORM_GOOD_ZONE_SIZE,
    COULROPHOBIA_SPEED_MULT,
    MADNESS_OFFSET_RANGE,
    MADNESS_DIRECTION_FLIP_CHANCE,
    MOD_MERCILESS_STORM,
    MOD_UNNERVING_PRESENCE,
    MOD_REVERSE,
    MOD_COULROPHOBIA,
    MOD_INSANITY,
)


class SkillCheckConfig:
    """Snapshot of all parameters for one skill check instance."""

    def __init__(self):
        self.pointer_speed: float = DEFAULT_POINTER_SPEED
        self.good_zone_size: float = DEFAULT_GOOD_ZONE_SIZE
        self.great_zone_size: float = DEFAULT_GREAT_ZONE_SIZE
        self.zone_start: float = random.uniform(0, 360)
        self.pointer_start: float = 0.0
        self.clockwise: bool = True
        self.reverse: bool = False
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.storm: bool = False
        self._place_pointer()

    def _place_pointer(self):
        """Start the pointer roughly opposite the zone so the user sees it approach."""
        zone_center = (self.zone_start + self.good_zone_size / 2) % 360
        offset = random.uniform(120, 240)
        self.pointer_start = (zone_center + offset) % 360


class SkillCheckEngine(QObject):
    """Orchestrates when and how skill checks are spawned."""

    skill_check_triggered = Signal(object)  # emits SkillCheckConfig

    # Signal emitted when a storm burst ends, so overlay can hide
    storm_ended = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_modifiers: set = set()
        self.speed_multiplier: float = 1.0
        self.zone_multiplier: float = 1.0
        self.min_interval: float = DEFAULT_MIN_INTERVAL
        self.max_interval: float = DEFAULT_MAX_INTERVAL
        self.running: bool = False
        self._in_storm: bool = False
        self._storm_end_time: float = 0.0

        self._spawn_timer = QTimer(self)
        self._spawn_timer.setSingleShot(True)
        self._spawn_timer.timeout.connect(self._trigger_check)

    # ------------------------------------------------------------------
    def start(self):
        self.running = True
        self._in_storm = False
        self._schedule_next()

    def stop(self):
        self.running = False
        self._spawn_timer.stop()
        self._in_storm = False

    # ------------------------------------------------------------------
    def _schedule_next(self):
        if not self.running:
            return
        interval = random.uniform(self.min_interval, self.max_interval)
        self._spawn_timer.start(int(interval * 1000))

    def _trigger_check(self):
        if not self.running:
            return
        import time as _time
        # Start a storm burst if the modifier is active and we're not already in one
        if MOD_MERCILESS_STORM in self.active_modifiers and not self._in_storm:
            if random.random() < 0.35:          # ~35 % chance each spawn
                self._in_storm = True
                self._storm_end_time = _time.monotonic() + STORM_DURATION_MS / 1000
        config = self._build_config()
        self.skill_check_triggered.emit(config)

    # ------------------------------------------------------------------
    def _build_config(self) -> SkillCheckConfig:
        cfg = SkillCheckConfig()
        cfg.pointer_speed = DEFAULT_POINTER_SPEED * self.speed_multiplier
        cfg.good_zone_size = DEFAULT_GOOD_ZONE_SIZE * self.zone_multiplier
        cfg.great_zone_size = DEFAULT_GREAT_ZONE_SIZE * self.zone_multiplier

        # --- Merciless Storm: narrow good-only zone, no great ---
        if self._in_storm:
            cfg.storm = True
            cfg.good_zone_size = STORM_GOOD_ZONE_SIZE
            cfg.great_zone_size = 0.0
            cfg.pointer_speed *= 1.2   # slightly faster during storm

        if MOD_UNNERVING_PRESENCE in self.active_modifiers:
            cfg.good_zone_size *= 0.6
            cfg.great_zone_size *= 0.6
            cfg.pointer_speed *= 1.3

        # --- Reverse: CCW rotation, great zone at START of good zone ---
        if MOD_REVERSE in self.active_modifiers:
            cfg.clockwise = False
            cfg.reverse = True

        # --- Coulrophobia: much faster, position stays centered ---
        if MOD_COULROPHOBIA in self.active_modifiers:
            cfg.pointer_speed *= COULROPHOBIA_SPEED_MULT

        # --- Madness (Insanity): random position & sometimes random direction ---
        if MOD_INSANITY in self.active_modifiers:
            cfg.offset_x = random.randint(-MADNESS_OFFSET_RANGE, MADNESS_OFFSET_RANGE)
            cfg.offset_y = random.randint(-MADNESS_OFFSET_RANGE // 2, MADNESS_OFFSET_RANGE // 2)
            if random.random() < MADNESS_DIRECTION_FLIP_CHANCE:
                cfg.clockwise = not cfg.clockwise

        cfg._place_pointer()
        return cfg

    # ------------------------------------------------------------------
    def on_check_completed(self, result: str):
        """Called after overlay finishes showing a result."""
        if not self.running:
            return
        import time as _time
        if self._in_storm:
            if _time.monotonic() < self._storm_end_time:
                # Immediately fire next storm check
                self._trigger_check()
                return
            # Storm period expired — tell overlay to hide
            self._in_storm = False
            self.storm_ended.emit()
        self._schedule_next()
