# ==============================================================================
# puzzlegen/job_creator.py
#
# Plans a new puzzle “job” by:
#   - Choosing creative variables (palette, music, category)
#   - Generating a unique video_id (6-hex base + 3-char gene code)
#   - Creating jobs/<video_id>/ with a starter manifest.json
#
# All file paths and gene maps come from puzzle_config.
# ==============================================================================

import json
import random
import secrets
from pathlib import Path
from datetime import datetime, timezone

import puzzle_config as config


def choose_creative_variables() -> dict:
    """Select one option from each creative pool defined in config.

    Returns:
        dict: { "palette": str, "music_track": str, "category": str }
    """
    return {
        "palette": random.choice(config.CREATIVE_OPTIONS["palettes"]),
        "music_track": random.choice(config.CREATIVE_OPTIONS["music_tracks"]),
        "category": random.choice(config.CREATIVE_OPTIONS["categories"]),
    }


def generate_video_id(choices: dict) -> str:
    """Build a unique, human-auditable video ID.

    Format:
        <hex_base>-<gene_code>
        - hex_base: 6 uppercase hex chars from secrets.token_hex(3)
        - gene_code: 3 chars derived from config.GENE_MAP for
                     (palette, music_track, category), fallback 'X'

    Args:
        choices: Creative selections used to compute the gene code.

    Returns:
        str: e.g., "A1B2C3-012"
    """
    hex_base = secrets.token_hex(3).upper()
    palette_code = config.GENE_MAP["color_palette"].get(choices["palette"], "X")
    music_code = config.GENE_MAP["music_track"].get(choices["music_track"], "X")
    category_code = config.GENE_MAP["category"].get(choices["category"], "X")
    return f"{hex_base}-{palette_code}{music_code}{category_code}"


def create_job_folder_and_manifest(video_id: str, choices: dict) -> Path:
    """Create jobs/<video_id>/ and write a starter manifest.json.

    Args:
        video_id: The generated ID used as the folder name.
        choices: The creative selections to embed in the manifest.

    Returns:
        Path: Path to the created job directory.
    """
    job_dir = config.JOBS_DIR / video_id
    job_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "video_id": video_id,
        "status": {
            "puzzle_generated": False,
            "video_rendered": False,
            "video_uploaded": False,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "creative_choices": choices,
        "puzzle_file": "puzzle.json",
        "video_file": None,
    }

    (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=4), encoding="utf-8")
    return job_dir


def setup_new_job() -> Path:
    """High-level planner that assembles a job folder + manifest.

    Returns:
        Path: The path to the newly created job folder.
    """
    print("--- Setting up new job ---")
    choices = choose_creative_variables()
    print(f"   - Creative choices made: {choices}")

    video_id = generate_video_id(choices)
    print(f"   - Generated Video ID: {video_id}")

    job_folder_path = create_job_folder_and_manifest(video_id, choices)
    print(f"   - Created job folder and manifest at: {job_folder_path}")

    return job_folder_path
