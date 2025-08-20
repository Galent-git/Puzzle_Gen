"""
Automation Scheduler for Puzzle-to-YouTube Pipeline
---------------------------------------------------
This script automates the execution of the complete puzzle video pipeline:
1. Puzzle generation (puzzlegen.py)
2. Video rendering (reelgen.py)
3. YouTube upload (uploader.py)

Modes of Operation:
- RUN_ONCE: Executes the pipeline once and exits.
- SCHEDULE: Runs the pipeline daily at predefined times using the `schedule` package.
- TEST_RUN: Prints the commands without executing them.

Configuration:
- Paths to each script are set relative to the project root.
- RUN_TIME_1 / RUN_TIME_2 define daily run times for scheduled mode.
- All mode switches and times can be adjusted within the script.

Dependencies:
- Python 3.7+
- `schedule` package (for scheduled mode)

Usage:
    python scheduler.py          # Runs once if RUN_ONCE=True
    python scheduler.py --watch  # Requires custom CLI handling if desired
"""
#!/usr/bin/env python3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import schedule  # pip install schedule
except ImportError:
    schedule = None

# ── CONFIG ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PUZZLEGEN      = ROOT_DIR / "puzzlegen" / "puzzlegen.py"          # generates job folders
REELGEN        = ROOT_DIR / "reelgen" / "reelgen.py"            # renders jobs/<id>/video.mp4
YOUTUBE_UPLOAD = ROOT_DIR / "uploader" / "uploader.py"   # uploads one pending job

# System local time runs
RUN_TIME_1 = "07:00"
RUN_TIME_2 = "19:00"

# --- MODE SWITCHES ---
TEST_RUN   = False   # True = print commands, don't execute
RUN_ONCE   = True   # True = run pipeline once immediately, then exit
SCHEDULE   = False    # True = run pipeline on schedule

# ── UTIL ──────────────────────────────────────────────────────────────────────
import os

def run_script(path: Path, dry: bool = False) -> bool:
    if not path.exists():
        print(f"ERROR: Script not found: {path}")
        return False

    cmd = [sys.executable, str(path)]
    print(f"\n$ {' '.join(cmd)}")
    if dry:
        print("(dry run) — not executing")
        return True

    # Force UTF-8 in the child; decode robustly in the parent
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"             # Python-wide UTF-8 mode
    env["PYTHONIOENCODING"] = "utf-8"   # stdio encoding override

    try:
        # Change capture_output to False to see the live output
        res = subprocess.run(
            cmd,
            check=True,
            capture_output=False, # <--- CHANGE THIS
            # text=True,          # <--- Comment out or remove these
            # encoding="utf-8",
            # errors="replace",
            cwd=str(ROOT_DIR),    # <--- KEEP THE PREVIOUS FIX
            env=env,
        )
        # Since we are no longer capturing, these blocks won't do anything.
        # if res.stdout and res.stdout.strip():
        #     print(res.stdout.rstrip())
        # if res.stderr and res.stderr.strip():
        #     print(res.stderr.rstrip())
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"\n✖ FAILED: {path.name}")
        if e.stdout:
            print("--- stdout ---")
            print(e.stdout.rstrip())
        if e.stderr:
            print("--- stderr ---")
            print(e.stderr.rstrip())
        return False
    except Exception as e:
        print(f"\n✖ ERROR running {path.name}: {e}")
        return False


def job(dry: bool = False) -> None:
    print(f"\n>>> Pipeline start {datetime.now().isoformat()} <<<")
    if not run_script(PUZZLEGEN, dry): return
    if not run_script(REELGEN, dry): return
    if not run_script(YOUTUBE_UPLOAD, dry): return
    print(">>> Pipeline completed <<<")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Scripts:")
    print(f"  puzzlegen      → {PUZZLEGEN}")
    print(f"  reelgen        → {REELGEN}")
    print(f"  youtube_upload → {YOUTUBE_UPLOAD}")

    if RUN_ONCE:
        job(dry=TEST_RUN)
        sys.exit()

    if SCHEDULE:
        if schedule is None:
            raise SystemExit("The 'schedule' package is required for scheduled mode. Install with: pip install schedule")
        print(f"--- Automation Scheduler ---")
        print(f"Will run daily at {RUN_TIME_1} and {RUN_TIME_2}.")
        schedule.every().day.at(RUN_TIME_1).do(job, dry=TEST_RUN)
        schedule.every().day.at(RUN_TIME_2).do(job, dry=TEST_RUN)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting scheduler.")
