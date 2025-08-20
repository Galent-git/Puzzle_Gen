"""
YouTube Upload Configuration
----------------------------
Central configuration file for all YouTube upload settings.

Contents:
- PATH CONFIGURATION: Directories for project structure, credentials, and jobs.
- API CONFIGURATION: YouTube Data API name, version, and scopes.
- MASTER UPLOAD DEFAULTS: Centralized metadata for uploads including title format,
  description, tags, category, language, privacy settings, and more.

Usage:
    import upload_config
    print(upload_config.UPLOAD_DEFAULTS["title_format"])

This ensures all upload-related scripts share a single source of truth.
"""
# uploader/upload_config.py
from pathlib import Path

# --- PATH CONFIGURATION ---
ROOT_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = ROOT_DIR / "project"
OUTPUT_DIR = ROOT_DIR / "output"
CLIENT_SECRETS_FILE = SECRETS_DIR / "client_secrets.json"
TOKEN_PICKLE_PATH = SECRETS_DIR / "token.pickle"
JOBS_DIR = ROOT_DIR / "jobs"  # adjust if jobs live elsewhere

# --- API CONFIGURATION ---
API_NAME = "youtube"
API_VERSION = "v3"
# For uploads only, this is fine. If you also set thumbnails/extra metadata later, consider:
# SCOPES = ["https://www.googleapis.com/auth/youtube"]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# --- MASTER UPLOAD DEFAULTS (UNIFIED) ---
UPLOAD_DEFAULTS = {
    # --- Content Settings ---
    "title_format": "Puzzle // {category} // {id}",  
    "description": (
        "A new anomaly has been detected. Can you find the solution?\n\n"
        "#puzzle #riddle #brainteaser #retrogaming"
    ),
    "tags": [
        "puzzle", "riddle", "brain teaser", "logic puzzle", "shorts", "brain games"
    ],

    # --- YouTube Category & Language ---
    "categoryId": "20",  # 20 = Gaming
    "defaultLanguage": "en",
    "defaultAudioLanguage": "en",

    # --- Status and Privacy ---
    "privacyStatus": "private",  # "private", "public", or "unlisted"
    "license": "youtube",
    "embeddable": True,
    # Removed unused "madeForKids" to avoid confusion
    "selfDeclaredMadeForKids": False,
    "notifySubscribers": True,
}