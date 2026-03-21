"""Configuration constants for SkillCheck Trainer."""

# Default hotkey
DEFAULT_HOTKEY = "space"

# Skill check timing
DEFAULT_POINTER_SPEED = 270.0   # degrees per second
DEFAULT_GOOD_ZONE_SIZE = 45.0   # degrees of arc
DEFAULT_GREAT_ZONE_SIZE = 12.0  # degrees of arc (at end of good zone)
DEFAULT_MIN_INTERVAL = 5.0      # seconds between skill checks
DEFAULT_MAX_INTERVAL = 15.0

SKILL_CHECK_TIMEOUT_BUFFER = 300  # ms extra after one revolution

# Overlay visuals
OVERLAY_SIZE = 400
RING_RADIUS = 130
RING_WIDTH = 24
POINTER_LENGTH = 155

# Animation
ANIMATION_FPS = 60
ANIMATION_INTERVAL = 1000 // ANIMATION_FPS  # ~16 ms

# Result display
RESULT_DISPLAY_MS = 600
WARNING_DURATION_MS = 200

# Merciless Storm
STORM_DURATION_MS = 10000       # 10 seconds of continuous checks
STORM_DELAY_MS = 400             # tiny gap between storm checks
STORM_GOOD_ZONE_SIZE = 20.0      # narrow good-only zone during storm

# Coulrophobia
COULROPHOBIA_SPEED_MULT = 2.0    # how much faster skill checks become

# Madness (Insanity)
MADNESS_OFFSET_RANGE = 250       # max px offset from center
MADNESS_DIRECTION_FLIP_CHANCE = 0.5

# Modifier IDs
MOD_MERCILESS_STORM = "merciless_storm"
MOD_UNNERVING_PRESENCE = "unnerving_presence"
MOD_REVERSE = "reverse"
MOD_COULROPHOBIA = "coulrophobia"
MOD_INSANITY = "insanity"

# Colors (R, G, B, A)
COLOR_RING_BG = (60, 60, 70, 255)
COLOR_GOOD_ZONE = (230, 180, 40, 255)
COLOR_GREAT_ZONE = (255, 255, 255, 255)
COLOR_POINTER = (220, 40, 40, 255)
COLOR_OVERLAY_BG = (10, 10, 20, 180)
COLOR_RESULT_GREAT = (255, 215, 0, 255)
COLOR_RESULT_GOOD = (200, 200, 60, 255)
COLOR_RESULT_FAIL = (220, 50, 50, 255)
