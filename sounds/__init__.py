"""Sound manager for SkillCheck Trainer — plays cue and result sounds."""

import os

from PySide6.QtCore import QUrl, QObject
from PySide6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput

_SOUNDS_DIR = os.path.dirname(os.path.abspath(__file__))


class SoundManager(QObject):
    """Manages playback of skill-check audio cues."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Cue sound (.wav) — QSoundEffect for low latency
        self._cue = QSoundEffect(self)
        cue_path = os.path.join(_SOUNDS_DIR, "skillcheck_sound_cue.wav")
        self._cue.setSource(QUrl.fromLocalFile(cue_path))
        self._cue.setVolume(0.8)

        # Result sounds (.mp3) — QMediaPlayer per sound
        self._players: dict[str, tuple[QMediaPlayer, QAudioOutput]] = {}
        for name in ("good", "great", "fail"):
            player = QMediaPlayer(self)
            output = QAudioOutput(self)
            output.setVolume(0.8)
            player.setAudioOutput(output)
            path = os.path.join(_SOUNDS_DIR, f"skillcheck_{name}.mp3")
            player.setSource(QUrl.fromLocalFile(path))
            self._players[name] = (player, output)

        # Jumpscare sound
        self._jumpscare_player = QMediaPlayer(self)
        self._jumpscare_output = QAudioOutput(self)
        self._jumpscare_output.setVolume(1.0)
        self._jumpscare_player.setAudioOutput(self._jumpscare_output)
        js_path = os.path.join(_SOUNDS_DIR, "jumpscare.mp3")
        if os.path.isfile(js_path):
            self._jumpscare_player.setSource(QUrl.fromLocalFile(js_path))

    def play_cue(self):
        """Play the skill-check approach cue."""
        self._cue.play()

    def play_result(self, result: str):
        """Play the sound for a given result ('great', 'good', 'fail', or 'miss')."""
        key = result if result in self._players else "fail"
        player, _ = self._players[key]
        player.stop()
        player.setPosition(0)
        player.play()

    def play_jumpscare(self):
        """Play the jumpscare sound effect."""
        self._jumpscare_player.stop()
        self._jumpscare_player.setPosition(0)
        self._jumpscare_player.play()
