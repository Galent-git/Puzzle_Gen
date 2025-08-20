# PuzzleGen : From AI generated Puzzles to YouTube Shorts

A fully automated content pipeline that:
- Generates bite-sized logic puzzles using Google's GenAI.
- Utilizes localized manifest logs for each puzzle to keep track of the stage of production.
- Transforms them into animated vertical reels (typing effect, glitches, music).
- Publishes directly to YouTube, ready for viewers.
- Designed for clean separation of stages, robust state tracking, and effortless daily operation.
- Can be automated and scheduled at any desired time or be run as a one off together or by individual stage.

> **Note:** This is a clean demo repository for showcase purposes, not the private production repo.

---

## Watch the Output
YouTube: [@Ymainframeriot](https://www.youtube.com/@Ymainframeriot)
Article: (https://open.substack.com/pub/almostreal/p/python-puzzles-youtube-and-ai-a-twist?r=5d4j0q&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true)

---

## Why I Built This
- Automate repetitive tasks: prompting, layout, rendering, uploading.
- Experiment with **A/B testing** at the video assembly level (palettes, music).
- Practice **production-grade automation** with clear state boundaries.
- Combine AI-assisted coding with my passion for puzzles and creative building.
- Deepen my knowledge of Python and integrated workflows.

---

## Pipeline at a Glance

[ puzzlegen ] --> [ reelgen ] --> [ audio_mux ] --> [ uploader ] -- [ scheduler ]
   JSON out         1080x1920        bg music          publish         automate


| Stage | Script | Description |
|-------|--------|-------------|
| **1) Puzzle Generation (AI)** | `puzzlegen.py` | Calls Google GenAI with curated prompts from `prompts.json` to produce strictly formatted puzzles. Output appended to `assets/puzzles_data.json`. |
| **2) Reel Rendering (Video)** | `reelgen.py` | Picks a puzzle and renders a 1080×1920 vertical reel with typing animation, glitches, countdown, reveal, explanation, and sign-off. Randomizes palette & music per run, encoded via **gene map** in filename. |
| **3) Audio Muxing** | `audio_mux.py` | Adds background music with FFmpeg, ensuring clean audio integration. |
| **4) YouTube Upload (Publish)** | `uploader.py` | Scan the jobs directory,reads manifest files, uploads the next pending video via YouTube Data API v3 and applies chosen metadata. |
| **5) Scheduling / Orchestration** | `scheduler.py` | Optional automation to chain generation → rendering → upload on a schedule. |

---


## Data Format (puzzles)

Each puzzle is stored as a flat JSON object. Example:

```json
{
    "puzzle_lines_with_error": [
        "2 -> 8",
        "3 -> 15",
        "5 -> 35",
        "6 -> 40"
    ],
    "text_of_erroneous_line": "6 -> 40",
    "category": "Number Logic",
    "explanation": "The rule is Y = X * (X+2). For X=6, the result should be 6 * 8 = 48.",
    "id": "5C81E6-324"
}
```

## Tech Stack
- **AI Generation:** Google GenAI SDK (`google-genai`)
- **Video & Text Rendering:** MoviePy, Pillow
- **Audio Integration:** FFmpeg
- **Publishing:** YouTube Data API (`google-api-python-client`)

---

## Limitations & Future Ideas
- More puzzle categories and weighted prompt selection.
- Audio normalization & beat-synced transitions.
- Batch rendering & upload queues.
- Dashboard or web UI to monitor youtube performance metrics in real-time.
- Automatic Performance Analysis of design choices and auto adjustment of pipeline.
- Mobile or Browser game that follows the same theme.
---

## Legal / Usage
This demo and the associated YouTube channel are provided for showcase purposes.  
Replication of the channel’s content or reuse of this codebase for publication is **not permitted**.  
If you intend to experiment privately, do so respectfully and without republishing outputs.
