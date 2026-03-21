from pynput import keyboard as kb
from PySide6.QtCore import QObject, Signal, QCoreApplication, QEvent


class _KeyEvent(QEvent):
    """Thread-safe custom event posted from the pynput listener thread."""
    TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self):
        super().__init__(self.TYPE)


class GlobalListener(QObject):
    """Listens for a configurable global hotkey using pynput."""

    key_pressed = Signal()

    SPECIAL_KEYS = {
        "space": kb.Key.space,
        "shift": kb.Key.shift,
        "shift_l": kb.Key.shift,
        "shift_r": kb.Key.shift_r,
        "ctrl": kb.Key.ctrl_l,
        "ctrl_l": kb.Key.ctrl_l,
        "ctrl_r": kb.Key.ctrl_r,
        "alt": kb.Key.alt_l,
        "alt_l": kb.Key.alt_l,
        "alt_r": kb.Key.alt_r,
        "tab": kb.Key.tab,
        "enter": kb.Key.enter,
        "esc": kb.Key.esc,
        "f1": kb.Key.f1,
        "f2": kb.Key.f2,
        "f3": kb.Key.f3,
        "f4": kb.Key.f4,
        "f5": kb.Key.f5,
        "f6": kb.Key.f6,
        "f7": kb.Key.f7,
        "f8": kb.Key.f8,
        "f9": kb.Key.f9,
        "f10": kb.Key.f10,
        "f11": kb.Key.f11,
        "f12": kb.Key.f12,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_key = kb.Key.space
        self.target_key_name: str = "space"
        self.active: bool = False
        self._listener: kb.Listener | None = None

    # ------------------------------------------------------------------
    def set_key(self, key_name: str):
        key_name = key_name.lower().strip()
        self.target_key_name = key_name
        if key_name in self.SPECIAL_KEYS:
            self.target_key = self.SPECIAL_KEYS[key_name]
        elif len(key_name) == 1:
            self.target_key = kb.KeyCode.from_char(key_name)
        else:
            # Fallback
            self.target_key = kb.Key.space
            self.target_key_name = "space"

    # ------------------------------------------------------------------
    def start(self):
        if self._listener is not None:
            return
        self._listener = kb.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    # ------------------------------------------------------------------
    def _on_press(self, key):
        if not self.active:
            return
        match = False
        if isinstance(self.target_key, kb.Key):
            match = key == self.target_key
        elif isinstance(self.target_key, kb.KeyCode):
            if isinstance(key, kb.KeyCode) and key.char is not None:
                match = key.char.lower() == self.target_key.char.lower()
        if match:
            # Thread-safe: post event to the Qt event loop
            QCoreApplication.postEvent(self, _KeyEvent())

    def event(self, ev):
        if ev.type() == _KeyEvent.TYPE:
            self.key_pressed.emit()
            return True
        return super().event(ev)
