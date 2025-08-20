"""
Uploader Script for YouTube Puzzle Videos
-----------------------------------------
This module handles the upload of rendered puzzle videos to YouTube using the YouTube Data API v3.

Workflow:
1. Scans the jobs directory for completed but not-yet-uploaded videos.
2. Authenticates with the YouTube API (via `auth.py`).
3. Prepares metadata using centralized defaults from `upload_config.py`.
4. Uploads the selected video to YouTube.
5. Updates the job's `manifest.json` with upload status and YouTube video ID.

Usage:
    python uploader.py
        - Uploads a single pending job to YouTube.

Dependencies:
    - google-api-python-client
    - OAuth 2.0 credentials
    - Properly formatted `manifest.json` for each job
"""
# uploader/main_uploader.py
"""
This script uploads a single video file to YouTube.
"""
import json
from pathlib import Path
import datetime
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import upload_config
import auth

JOBS_DIR = upload_config.JOBS_DIR
def _load_manifest(job_dir: Path) -> dict:
    with open(job_dir / "manifest.json", "r", encoding="utf-8") as f:
        return json.load(f)

def _save_manifest(job_dir: Path, manifest: dict) -> None:
    with open(job_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
def upload_video_to_youtube(video_path: Path):
    """
    Handles the core logic of uploading a single video to YouTube.
    """
    try:
        # 1. AUTHENTICATION
        print("--- Step 1: Authenticating ---")
        youtube_service = auth.get_authenticated_service()

        # 2. METADATA PREPARATION
        print("\n--- Step 2: Preparing Video Metadata ---")
        
        # Get the single, unified defaults dictionary from the config file.
        defaults = upload_config.UPLOAD_DEFAULTS
        
        # Extract an ID from the filename.
        video_id_from_filename = video_path.stem.split('_')[0]

        # Build the title using the format string from our defaults.
        # Load metadata from manifest if available
        category = manifest.get("category", "Logic")
        

        # Build the title using the format string from our defaults
        title = defaults["title_format"].format(
        category=category,
        id=video_id_from_filename)
        print(f"Title: {title}")

        # Assemble the complete request body using our single defaults dictionary.
        body = {
            "snippet": {
                "title": title,
                "description": defaults["description"], # Using the defaults dictionary
                "tags": defaults["tags"],               # Using the defaults dictionary
                "categoryId": defaults["categoryId"],     # FIXED: Now finds the key
                "defaultLanguage": defaults["defaultLanguage"],
                "defaultAudioLanguage": defaults["defaultAudioLanguage"]
            },
            "status": {
                "privacyStatus": defaults["privacyStatus"],
                "license": defaults["license"],
                "embeddable": defaults["embeddable"],
                "selfDeclaredMadeForKids": defaults["selfDeclaredMadeForKids"]
            }
        }

        # 3. UPLOAD EXECUTION
        print("\n--- Step 3: Starting Upload ---")
        with open(video_path, 'rb') as video_file_handle:
            media_body = MediaIoBaseUpload(
                video_file_handle, 
                mimetype='video/mp4', 
                chunksize=-1, 
                resumable=True
            )
            
            request = youtube_service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media_body,
                notifySubscribers=defaults["notifySubscribers"]
            )

            # Resumable upload loop
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%.")

        uploaded_video_id = response.get('id')
        print(f"\n✅ UPLOAD COMPLETE! Video ID: {uploaded_video_id}")
        print(f"Link: https://www.youtube.com/watch?v={uploaded_video_id}")
        return uploaded_video_id

    except FileNotFoundError:
        print(f"❌ ERROR: Video file not found at '{video_path}'.")
    except HttpError as e:
        print(f"❌ An HTTP error {e.resp.status} occurred:\n{e.content}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
from datetime import datetime
import json
from pathlib import Path



if __name__ == "__main__":
    print("--- YouTube Job Uploader (single job) ---")

    if not JOBS_DIR.exists():
        raise SystemExit(f"Jobs directory not found: {JOBS_DIR.resolve()}")

    # Gather candidates: rendered==true, video_uploaded==false, has video_file that exists
    candidates = []
    for d in sorted(JOBS_DIR.iterdir()):
        if not d.is_dir():
            continue
        man_path = d / "manifest.json"
        if not man_path.exists():
            continue
        try:
            manifest = _load_manifest(d)
        except Exception as e:
            print(f"Skipping {d.name}: bad manifest ({e})")
            continue

        status = manifest.get("status", {})
        if not status.get("video_rendered", False):
            continue
        if status.get("video_uploaded", False) is not False:
            # skip if already true or marked "failed" (change to `!= False` if you want to retry failures)
            continue

        video_file = manifest.get("video_file")
        if not video_file:
            continue
        video_path = d / video_file
        if not video_path.exists():
            continue

        # Prefer using created_at to pick the oldest; fallback to name sort
        created_at = manifest.get("created_at", "")
        candidates.append((created_at, d, manifest, video_path))

    if not candidates:
        print("No pending jobs found.")
        raise SystemExit()

    # Pick ONE job: oldest created_at first (empty strings sort first; adjust if you want latest)
    candidates.sort(key=lambda t: t[0])
    _, job_dir, manifest, video_path = candidates[0]

    print(f"\n— Uploading single job {job_dir.name}: {video_path.name}")
    try:
        yt_id = upload_video_to_youtube(video_path)
        manifest.setdefault("status", {})
        if yt_id:
            manifest["status"]["video_uploaded"] = True
            manifest["uploaded_at"] = datetime.now().isoformat()
            manifest["youtube_video_id"] = yt_id
            print(f"✅ Marked uploaded in {job_dir / 'manifest.json'}")
        else:
            manifest["status"]["video_uploaded"] = "failed"
            manifest["upload_error"] = "unknown upload result"
            manifest["upload_attempted_at"] = datetime.now().isoformat()
            print(f"⚠️ Marked failed in {job_dir / 'manifest.json'}")
    except Exception as e:
        manifest.setdefault("status", {})
        manifest["status"]["video_uploaded"] = "failed"
        manifest["upload_error"] = str(e)
        manifest["upload_attempted_at"] = datetime.now().isoformat()
        print(f"❌ Upload error for {job_dir.name}: {e}")
    finally:
        _save_manifest(job_dir, manifest)

    # Exit immediately: exactly one job handled per run
    print("\n--- Done (single job) ---")
