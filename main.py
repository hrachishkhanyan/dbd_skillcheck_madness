"""SkillCheck Trainer — Dead by Daylight–style skill checks invading your desktop."""

import sys
import os

# Ensure project root is on the path so relative imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from core.skillcheck_engine import SkillCheckEngine
from core.stats_tracker import StatsTracker
from input.global_listener import GlobalListener
from overlay.skillcheck_overlay import SkillCheckOverlay
from sounds import SoundManager
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep running in tray

    # Core objects
    stats = StatsTracker()
    engine = SkillCheckEngine()
    listener = GlobalListener()
    sounds = SoundManager()
    overlay = SkillCheckOverlay(sounds)

    # Engine → Overlay: trigger a new skill check
    engine.skill_check_triggered.connect(overlay.start_check)

    # Engine → Overlay: storm burst ended, hide the ring
    engine.storm_ended.connect(overlay.cancel)

    # Global key → Overlay: user pressed the hotkey
    listener.key_pressed.connect(overlay.on_key_pressed)

    # Overlay → Engine + Stats: a check finished (fires after result display)
    def on_check_completed(result: str, reaction_ms: float):
        stats.record(result, reaction_ms)
        engine.on_check_completed(result)

    overlay.check_completed.connect(on_check_completed)

    # Main control panel
    window = MainWindow(engine, overlay, listener, stats)
    window.show()

    # Start the global keyboard listener (always running; active flag gates it)
    listener.start()

    ret = app.exec()
    listener.stop()
    sys.exit(ret)


if __name__ == "__main__":
    main()
