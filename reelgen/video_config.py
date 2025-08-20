"""video_config.py — Video Rendering Configuration

This module stores constants and settings for puzzle video rendering, such as:
- Video dimensions and font settings.
- Color palettes for different visual themes.
- Animation speeds, timings, and layout positions.
- File paths for assets like fonts and music.

It is imported by reelgen.py and other modules to maintain consistent rendering styles.
"""

import string
from pathlib import Path

# -- General Settings
W, H = 1080, 1920
FPS = 30
FONT_PATH = Path("assets/DejaVuSansMono.ttf")

# -- Project Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
JOBS_DIR = PROJECT_ROOT / "jobs"
ASSETS_DIR = PROJECT_ROOT / "assets"
MUSIC_DIR = ASSETS_DIR

# -- Font Sizes
TITLE_FONT_SIZE = 75
PUZZLE_LINE_FONT_SIZE = 70
EXPLANATION_FONT_SIZE = 65
COUNTDOWN_FONT_SIZE = 180
SIGNOFF_FONT_SIZE = 70



# -- Countdown / Flow
PRE_COUNTDOWN_PAUSE_S = 0.0
COUNTDOWN_SECONDS = 5
REVEAL_TO_EXPLANATION_DELAY_S = 0.5
EXPLANATION_HOLD_DURATION_S = 1.5

# -- Sign-off / End Card
SIGNOFF_TYPING_SPEED_CPS = 30
SIGNOFF_HOLD_DURATION_S = 1.5
SIGNOFF_GAP_S = 0.2
SIGNOFF_LINES = [
    {"text": "WERE YOU SUCCESSFUL?", "y_pos": 400},
    {"text": "LIKE TO CONFIRM",      "y_pos": 500},
    {"text": "SUBSCRIBE FOR",        "y_pos": 1050},
    {"text": "FURTHER TESTING",      "y_pos": 1150},
]

# -- Style and Animation
TITLE_STROKE_WIDTH = 2
PUZZLE_STROKE_WIDTH = 2
EXPLANATION_TYPING_SPEED_CPS = 30
PUZZLE_TYPING_SPEED_CPS =3
TITLE_TYPING_SPEED_CPS = 3
CURSOR_CHAR = "█"
CURSOR_BLINK_RATE_HZ = 2
TEXT_GLITCH_ENABLED = True
TEXT_GLITCH_SPEED_HZ = 3
TEXT_GLITCH_MAX_AFFECTED_CHARS = 5
TEXT_GLITCH_CHAR_SET = string.ascii_uppercase + string.digits
MULTILINE_SPACING_FACTOR = 0.25
MAX_TEXT_WIDTH_PX = W - 100
LINE_START_Y = 700
MIN_VERTICAL_GAP_BETWEEN_PUZZLE_LINES = 40

# -- Color Palettes
COLOR_SCHEMES = {
    "ghost":       {"name": "Ghost",       "main": (0, 255, 160),  "bg": (0, 0, 0),    "glow": (0, 255, 160, 128)},
    "amber":       {"name": "Amber",       "main": (255, 197, 51), "bg": (21, 13, 0),  "glow": (255, 176, 0, 160)},
    "ms_dos":      {"name": "MS-DOS",      "main": (220, 220, 220),"bg": (0, 0, 0),    "glow": (220, 220, 220, 100)},
    "ice":         {"name": "Ice",         "main": (193, 231, 255),"bg": (12, 20, 36), "glow": (90, 218, 255, 100)},
    "cyberpunk":   {"name": "Cyberpunk",   "main": (138, 43, 226), "bg": (15, 0, 15),  "glow": (255, 63, 232, 160)},
    "ultraviolet": {"name": "Ultraviolet", "main": (90, 218, 255), "bg": (2, 7, 18),   "glow": (0, 224, 255, 100)},
}
