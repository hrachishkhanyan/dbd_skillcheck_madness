from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QCheckBox,
    QSlider,
    QLabel,
    QComboBox,
    QSystemTrayIcon,
    QMenu,
    QFileDialog,
    QApplication,
)

from config import (
    MOD_MERCILESS_STORM,
    MOD_UNNERVING_PRESENCE,
    MOD_REVERSE,
    MOD_COULROPHOBIA,
    MOD_INSANITY,
    MOD_CHILL,
)

# ──────────────────────────── Dark stylesheet ────────────────────────────
STYLESHEET = """
QMainWindow, QWidget#central {
    background-color: #12122a;
}
QGroupBox {
    border: 1px solid #2a2a5a;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    color: #c8c8e0;
    font-weight: bold;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
}
QLabel {
    color: #c8c8e0;
    font-size: 12px;
}
QLabel#stat_value {
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
}
QPushButton {
    background-color: #1e1e42;
    border: 1px solid #3a3a6e;
    border-radius: 6px;
    padding: 8px 18px;
    color: #d0d0ee;
    font-size: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2e2e5a;
    border-color: #6a5acd;
}
QPushButton:pressed {
    background-color: #6a5acd;
}
QPushButton:disabled {
    background-color: #14142e;
    color: #555;
    border-color: #222;
}
QPushButton#start_btn {
    background-color: #1b5e20;
    border-color: #2e7d32;
}
QPushButton#start_btn:hover {
    background-color: #2e7d32;
}
QPushButton#stop_btn {
    background-color: #b71c1c;
    border-color: #c62828;
}
QPushButton#stop_btn:hover {
    background-color: #c62828;
}
QCheckBox {
    color: #c8c8e0;
    spacing: 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3a3a6e;
    border-radius: 4px;
    background: #14142e;
}
QCheckBox::indicator:checked {
    background: #6a5acd;
    border-color: #6a5acd;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #1e1e42;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #6a5acd;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #6a5acd;
    border-radius: 3px;
}
QComboBox {
    background-color: #1e1e42;
    border: 1px solid #3a3a6e;
    border-radius: 4px;
    padding: 4px 8px;
    color: #d0d0ee;
    font-size: 12px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e42;
    color: #d0d0ee;
    selection-background-color: #6a5acd;
}
"""


def _make_app_icon() -> QIcon:
    """Create a simple programmatic icon (purple ring)."""
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#6a5acd"))
    p.drawEllipse(4, 4, size - 8, size - 8)
    p.setBrush(QColor("#12122a"))
    p.drawEllipse(14, 14, size - 28, size - 28)
    p.setPen(QColor("#ff4444"))
    p.setFont(QFont("Segoe UI", 14, QFont.Bold))
    p.drawText(pm.rect(), Qt.AlignCenter, "SC")
    p.end()
    return QIcon(pm)


class MainWindow(QMainWindow):
    """Control-panel window for SkillCheck Trainer."""

    def __init__(self, engine, overlay, listener, stats, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.overlay = overlay
        self.listener = listener
        self.stats = stats

        self.setWindowTitle("SkillCheck Trainer")
        self.setFixedSize(420, 740)
        icon = _make_app_icon()
        self.setWindowIcon(icon)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(6)
        root.setContentsMargins(14, 14, 14, 14)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("⚡  SkillCheck Trainer")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#ffffff;")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Dead by Daylight–style skill checks … everywhere")
        subtitle.setStyleSheet("font-size:11px; color:#888;")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)

        # ── Start / Stop ──────────────────────────────────────
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶  START")
        self.start_btn.setObjectName("start_btn")
        self.stop_btn = QPushButton("⏹  STOP")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        root.addLayout(btn_row)

        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)

        # ── Modifiers ─────────────────────────────────────────
        mod_box = QGroupBox("Modifiers")
        mod_lay = QVBoxLayout(mod_box)
        self._mod_checks = {}
        modifiers = [
            (MOD_MERCILESS_STORM, "🔹 Merciless Storm — 10s burst, narrow zone"),
            (MOD_UNNERVING_PRESENCE, "🔹 Unnerving Presence — smaller zone, faster"),
            (MOD_REVERSE, "🔹 Reverse — counter-clockwise, great first"),
            (MOD_COULROPHOBIA, "🔹 Coulrophobia — very fast"),
            (MOD_INSANITY, "🔹 Madness — random position & direction"),
            (MOD_CHILL, "🔹 Chill — very rare skill checks (~5 min)"),
        ]
        for mod_id, label in modifiers:
            cb = QCheckBox(label)
            cb.toggled.connect(lambda checked, m=mod_id: self._on_mod_toggled(m, checked))
            mod_lay.addWidget(cb)
            self._mod_checks[mod_id] = cb

        # Jumpscare toggle (separate from game modifiers)
        mod_lay.addSpacing(6)
        self._jumpscare_cb = QCheckBox("💀 Jumpscare — fullscreen scare on fail")
        self._jumpscare_cb.toggled.connect(self._on_jumpscare_toggled)
        mod_lay.addWidget(self._jumpscare_cb)

        root.addWidget(mod_box)

        # ── Settings ──────────────────────────────────────────
        set_box = QGroupBox("Settings")
        set_lay = QVBoxLayout(set_box)

        # Speed slider
        self.speed_label = QLabel("Pointer Speed:  1.0×")
        set_lay.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 300)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self._on_speed)
        set_lay.addWidget(self.speed_slider)

        # Zone size slider
        self.zone_label = QLabel("Zone Size:  1.0×")
        set_lay.addWidget(self.zone_label)
        self.zone_slider = QSlider(Qt.Horizontal)
        self.zone_slider.setRange(10, 250)
        self.zone_slider.setValue(100)
        self.zone_slider.valueChanged.connect(self._on_zone)
        set_lay.addWidget(self.zone_slider)

        # Frequency slider
        self.freq_label = QLabel("Spawn Freq:  medium")
        set_lay.addWidget(self.freq_label)
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 100)
        self.freq_slider.setValue(50)
        self.freq_slider.valueChanged.connect(self._on_freq)
        set_lay.addWidget(self.freq_slider)

        # Keybinding
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Hotkey:"))
        self.key_combo = QComboBox()
        keys = (
            ["SPACE"]
            + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
            + [f"F{i}" for i in range(1, 13)]
            + ["SHIFT", "CTRL", "ALT", "TAB", "ENTER"]
        )
        self.key_combo.addItems(keys)
        self.key_combo.currentTextChanged.connect(self._on_key_changed)
        key_row.addWidget(self.key_combo)
        set_lay.addLayout(key_row)

        root.addWidget(set_box)

        # ── Stats ─────────────────────────────────────────────
        stat_box = QGroupBox("Statistics")
        stat_lay = QVBoxLayout(stat_box)

        self.stat_accuracy = self._stat_row(stat_lay, "Accuracy")
        self.stat_breakdown = self._stat_row(stat_lay, "Great / Good / Fail")
        self.stat_streak = self._stat_row(stat_lay, "Best Streak")
        self.stat_reaction = self._stat_row(stat_lay, "Avg Reaction")

        stat_btn_row = QHBoxLayout()
        export_btn = QPushButton("Export JSON")
        export_btn.clicked.connect(self._export_stats)
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_stats)
        stat_btn_row.addWidget(export_btn)
        stat_btn_row.addWidget(reset_btn)
        stat_lay.addLayout(stat_btn_row)

        root.addWidget(stat_box)

        # ── Tray button ────────────────────────────────────────
        tray_btn = QPushButton("Minimize to Tray")
        tray_btn.clicked.connect(self._minimize_to_tray)
        root.addWidget(tray_btn)

        root.addStretch()

        # ── System tray icon ──────────────────────────────────
        self.tray = QSystemTrayIcon(icon, self)
        tray_menu = QMenu()
        tray_menu.addAction("Show", self._restore_from_tray)
        tray_menu.addSeparator()
        tray_menu.addAction("Start", self._on_start)
        tray_menu.addAction("Stop", self._on_stop)
        tray_menu.addSeparator()
        tray_menu.addAction("Quit", QApplication.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        # ── Periodic stats refresh ────────────────────────────
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(500)

    # ==================================================================
    # Helpers
    # ==================================================================
    @staticmethod
    def _stat_row(layout, label_text):
        row = QHBoxLayout()
        lbl = QLabel(f"{label_text}:")
        val = QLabel("—")
        val.setObjectName("stat_value")
        val.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        layout.addLayout(row)
        return val

    # ==================================================================
    # Slots
    # ==================================================================
    def _on_start(self):
        self.engine.start()
        self.listener.active = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_stop(self):
        self.engine.stop()
        self.overlay.cancel()
        self.listener.active = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_mod_toggled(self, mod_id, checked):
        if checked:
            self.engine.active_modifiers.add(mod_id)
        else:
            self.engine.active_modifiers.discard(mod_id)

    def _on_jumpscare_toggled(self, checked):
        self.overlay.jumpscare_enabled = checked

    def _on_speed(self, value):
        mult = value / 100.0
        self.speed_label.setText(f"Pointer Speed:  {mult:.1f}×")
        self.engine.speed_multiplier = mult

    def _on_zone(self, value):
        mult = value / 100.0
        self.zone_label.setText(f"Zone Size:  {mult:.1f}×")
        self.engine.zone_multiplier = mult

    def _on_freq(self, value):
        t = (value - 1) / 99.0  # 0..1
        min_i = 15.0 - 14.0 * t   # 15 → 1
        max_i = 25.0 - 22.0 * t   # 25 → 3
        self.engine.min_interval = max(min_i, 1.0)
        self.engine.max_interval = max(max_i, min_i + 1.0)
        labels = {0: "very rare", 25: "rare", 50: "medium", 75: "frequent", 100: "rapid"}
        closest = min(labels, key=lambda k: abs(k - value))
        self.freq_label.setText(f"Spawn Freq:  {labels[closest]}")

    def _on_key_changed(self, text):
        self.listener.set_key(text.lower())
        self.overlay.hotkey_label = text.upper()

    # ── Stats ─────────────────────────────────────────────
    def _refresh_stats(self):
        s = self.stats
        self.stat_accuracy.setText(f"{s.accuracy:.1f}%")
        self.stat_breakdown.setText(f"{s.greats}  /  {s.goods}  /  {s.fails + s.misses}")
        self.stat_streak.setText(f"{s.best_streak}")
        self.stat_reaction.setText(
            f"{s.avg_reaction_ms:.0f} ms" if s.avg_reaction_ms else "—"
        )

    def _export_stats(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Stats", "skillcheck_stats.json", "JSON (*.json)"
        )
        if path:
            self.stats.export_json(path)

    def _reset_stats(self):
        self.stats.reset()
        self._refresh_stats()

    # ── Tray ──────────────────────────────────────────────
    def _minimize_to_tray(self):
        self.hide()
        self.tray.showMessage(
            "SkillCheck Trainer",
            "Running in the background. Right-click tray icon for options.",
            QSystemTrayIcon.Information,
            2000,
        )

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._restore_from_tray()

    def closeEvent(self, event):  # noqa: N802
        event.ignore()
        self._minimize_to_tray()
