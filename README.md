# ⚡ SkillCheck Trainer

### *Because spreadsheets don't have skill checks. Yet.*

---

Tired of your mundane 9-to-5? Miss the rush of repairing generators under pressure while a shadowy figure breathes down your neck? Wish your Tuesday afternoon standup came with a quick-time event?

**We got you.**

SkillCheck Trainer brings Dead by Daylight–style skill checks to your desktop — popping up at random while you work, browse, or pretend to work. Hit the hotkey in the zone or suffer the shame of a public `FAIL` floating above your spreadsheet.

> *"I just wanted to practice skill checks"* — you, explaining to your manager why there's a red overlay on your screen during a Zoom call.

---

## ✨ Features

- 🎯 **Always-on-top overlay** — transparent, click-through dial renders over *anything*, including borderless-fullscreen games
- ⌨️ **Global hotkey** — detects your keypress even when the app isn't focused (default: SPACE)
- 📊 **Full stat tracking** — Great / Good / Fail / Miss counts, accuracy %, reaction times, streaks
- 🔊 **Sound cues** — hear the skill check coming, celebrate greats, mourn fails
- 🎚️ **Difficulty sliders** — pointer speed, zone size, spawn frequency
- 💾 **JSON export** — prove to your friends you're cracked (or don't)
- 🖥️ **System tray** — hides quietly, strikes randomly

---

## 🩸 Modifiers

Because normal skill checks are for survivors who haven't prestiged.

| Modifier | What It Does |
|---|---|
| **Merciless Storm** | 10-second burst of uninterrupted, narrow skill checks. No great zone. No mercy. The ring doesn't leave your screen. Good luck. |
| **Unnerving Presence** | 40% smaller zones, 30% faster pointer. The Entity appreciates your suffering. |
| **Reverse** | Counter-clockwise rotation with the great zone flipped to the front. Your muscle memory is now useless. |
| **Coulrophobia** | *Very* fast. Like, unreasonably fast. Clown main energy. |
| **Madness** | Skill checks pop up at random positions on screen with random direction. Doctor says hello. |

Modifiers stack — enable several at once if you enjoy pain.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (tested on 3.11 / 3.12)
- **Windows 10 / 11**

### 1. Clone & set up

```powershell
cd SkillcheckApp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run

```powershell
python main.py
```

Click **▶ START**, go about your day, and try not to flinch when the cue sound plays.

---

## 📦 Building an Executable

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name SkillCheckTrainer --icon=NUL main.py
```

Find your `.exe` in the `dist/` folder. Distribute to coworkers at your own risk.

---

## 🗂️ Project Structure

```
SkillcheckApp/
├── main.py                        # Entry point
├── config.py                      # All tunable constants
├── requirements.txt
├── core/
│   ├── skillcheck_engine.py       # Spawn timing, modifier logic
│   └── stats_tracker.py           # Accuracy, streaks, reaction times, JSON export
├── input/
│   └── global_listener.py         # Global hotkey via pynput (thread-safe → Qt)
├── overlay/
│   └── skillcheck_overlay.py      # Full-screen transparent overlay + QPainter rendering
├── sounds/
│   ├── __init__.py                # SoundManager (cue + result sounds)
│   ├── skillcheck_sound_cue.wav
│   ├── skillcheck_good.mp3
│   ├── skillcheck_great.mp3
│   └── skillcheck_fail.mp3
└── ui/
    └── main_window.py             # Control panel + system tray
```

---

## ⚙️ Configuration

All defaults live in `config.py`. The UI sliders override speed, zone size, and spawn frequency at runtime.

---

## 📜 License

MIT — use it, mod it, bring it to your next LAN party.

---

*No generators were harmed in the making of this software. Several deadlines, however, were missed.*
