# ==============================================================================
# puzzlegen/puzzlegen.py
#
# Copyright 2025
#
# Orchestrates the creation of puzzle “jobs”:
#   1) Delegates job folder + manifest creation to job_creator.
#   2) Requests a category-specific puzzle from llm_handler (with retries).
#   3) Persists the puzzle to jobs/<id>/puzzle.json and updates manifest status.
#
# ==============================================================================

import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Local modules (config drives all paths/env)
import puzzle_config as config
import job_creator
import llm_handler

# Load .env (GOOGLE_API_KEY, etc.) from the path defined in config.
load_dotenv(dotenv_path=config.ENV_FILE_PATH)


def main() -> None:
    """Entry point for batch puzzle job generation.

    Parses the `--number` argument, then for each job:
      - prepares a jobs/<id>/ manifest via job_creator,
      - attempts puzzle generation via llm_handler with retries,
      - writes the puzzle JSON and updates manifest status flags.

    Side effects:
        Creates directories and files under config.JOBS_DIR.
        Writes/updates manifest.json and puzzle.json within each job.
    """
    parser = argparse.ArgumentParser(description="Generate new puzzle jobs.")
    parser.add_argument("--number", type=int, default=1, help="Number of new jobs to create.")
    args = parser.parse_args()

    print(f"--- Attempting to generate {args.number} new puzzle job(s) ---")
    successful_jobs = 0

    for i in range(args.number):
        print(f"\n--- Starting Job {i + 1} of {args.number} ---")

        # 1) Plan the job folder + manifest
        job_folder: Path = job_creator.setup_new_job()

        # Load manifest to retrieve category and video_id
        manifest_path = job_folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        chosen_category = manifest["creative_choices"]["category"]
        video_id = manifest["video_id"]

        # 2) Generate the puzzle via LLM (retry loop)
        print(f"\n--- Generating puzzle for job: {video_id} ---")
        puzzle_data = None
        for attempt in range(config.MAX_GENERATION_ATTEMPTS):
            print(f"   - LLM Attempt {attempt + 1} of {config.MAX_GENERATION_ATTEMPTS}...")
            attempt_data = llm_handler.generate_puzzle_from_llm(category=chosen_category)
            if attempt_data and llm_handler.validate_puzzle_structure(attempt_data):
                print("   - ✅ Success! Puzzle is valid.")
                puzzle_data = attempt_data
                break

        # 3) Finalize the job (persist + status update)
        if puzzle_data:
            print(f"\n--- Finalizing job {video_id} ---")

            # Use deterministic video_id as canonical puzzle id
            puzzle_data["id"] = video_id

            puzzle_file_path = job_folder / manifest["puzzle_file"]
            puzzle_file_path.write_text(json.dumps(puzzle_data, indent=4), encoding="utf-8")
            print(f"   - Puzzle saved to: {puzzle_file_path}")

            manifest["status"]["puzzle_generated"] = True
            manifest_path.write_text(json.dumps(manifest, indent=4), encoding="utf-8")
            print("   - Manifest updated: puzzle_generated = True")

            print(f"\n✅ Job {video_id} is ready for rendering.")
            successful_jobs += 1
        else:
            print(f"\n❌ LLM generation failed for job {video_id} after {config.MAX_GENERATION_ATTEMPTS} attempts.")
            manifest["status"]["puzzle_generated"] = "FAILED"
            manifest_path.write_text(json.dumps(manifest, indent=4), encoding="utf-8")

    print(f"\n--- Puzzlegen Run Complete: {successful_jobs} / {args.number} jobs created successfully. ---")


if __name__ == "__main__":
    main()
