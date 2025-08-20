
# puzzlegen/puzzle_config.py

from pathlib import Path

# --- PATHS ---

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent 
ASSETS_DIR = PROJECT_ROOT / "assets"
ENV_FILE_PATH = PROJECT_ROOT / "project" / ".env"
PROMPT_LIBRARY_PATH = SCRIPT_DIR / "prompts.json"
MODEL_NAME = "gemini-2.0-flash"
MAX_GENERATION_ATTEMPTS = 3
JOBS_DIR = PROJECT_ROOT / "jobs"


# --- CREATIVE CHOICES ---

CREATIVE_OPTIONS = {
    "palettes": ["ghost", "amber", "ms_dos", "ice", "cyberpunk","ultraviolet"],
    "music_tracks": [
        "track_A.mp3", "track_B.mp3", "track_C.mp3", 
        "track_D.mp3", "track_E.mp3", "track_F.mp3"
    ],
    "categories": [
        "Arithmetic", "Wordplay", "Sequences", "Number Logic", "Observation"
    ]
}


# --- VIDEO ID "GENE MAP" ---
# This dictionary defines the encoding scheme for the video ID's gene code.
# It allows us to create a unique, trackable ID for each video.
GENE_MAP = {
    "color_palette": {
        "ghost": "0", "amber": "1", "ms_dos": "2", 
        "ice": "3", "cyberpunk": "4", "ultraviolet":"5"
    },
    "music_track": {
        "track_A.mp3": "0", "track_B.mp3": "1", "track_C.mp3": "2",
        "track_D.mp3": "3", "track_E.mp3": "4", "track_F.mp3": "5"
    },
    "category": {
        "Arithmetic": "0", "Wordplay": "1", "Observation": "2",
        "Sequences": "3", "Number Logic": "4"
    }
}

REQUIRED_PUZZLE_KEYS = { 
    "PUZZLE_LINES_WITH_ERROR", 
    "TEXT_OF_ERRONEOUS_LINE", 
    "CATEGORY", 
    "EXPLANATION"
}