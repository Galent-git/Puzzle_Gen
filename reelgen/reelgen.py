"""reelgen.py — Puzzle Video Rendering Pipeline

This module handles rendering puzzle videos with animated text, countdowns, and sign-off sequences
using MoviePy and PIL. It:
- Loads puzzle and manifest data from job folders.
- Wraps and renders text with glitch and cursor effects.
- Composes multiple animated text clips into a full puzzle video.
- Optionally muxes background music using audio_mux.
- Updates the job manifest after rendering.

Typical usage:
    from reelgen import process_job
    process_job(Path("jobs/my_puzzle_job"))
"""

import json, textwrap, random
from pathlib import Path

import numpy as np
from moviepy import VideoClip, CompositeVideoClip, ColorClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

import video_config

# ─────────────────────────── Title formatting config ─────────────────────────── #
# Edit in one place or override in video_config.TITLE_TEMPLATE
DEFAULT_TITLE_TEMPLATE = "EXP_{video_id} //\n {category} // \n FIND THE ANOMALY"


def make_video_title(manifest: dict, puzzle: dict, job_dir: Path) -> str:
    """Construct the on-screen title line.
    Pulls video_id from manifest, category from puzzle or creative_choices.
    Falls back to job dir name and 'Unknown'.
    Override template via video_config.TITLE_TEMPLATE if desired.
    """
    video_id = (
        manifest.get("video_id")
        or manifest.get("id")
        or manifest.get("videoId")
        or job_dir.name
    )
    cc = (manifest.get("creative_choices") or {})
    category = (
        puzzle.get("category")
        or cc.get("category")
        or cc.get("puzzle_category")
        or "Unknown"
    )
    template = getattr(video_config, "TITLE_TEMPLATE", DEFAULT_TITLE_TEMPLATE)
    try:
        return template.format(video_id=video_id, category=category)
    except Exception:
        # If a custom template is broken, fall back safely
        return f"EXP_{video_id} // {category} // FIND THE ANOMALY"


# ─────────────────────────── Helpers: I/O & Config ─────────────────────────── #

def _load_manifest(job_dir: Path) -> dict:
    m = job_dir / "manifest.json"
    with open(m, "r", encoding="utf-8") as f:
        return json.load(f)
def _save_manifest(job_dir: Path, manifest: dict) -> None:
    with open(job_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def _select_palette(manifest: dict):
    name = (manifest.get("creative_choices") or {}).get("palette")
    if name in video_config.COLOR_SCHEMES:
        return video_config.COLOR_SCHEMES[name]
    # fallback to your default active palette
    return video_config.COLOR_SCHEMES.get(getattr(video_config, "ACTIVE_PALETTE", "ghost"))


def _select_music(manifest: dict, assets_dir: Path | None = None) -> Path | None:
    assets_dir = assets_dir or getattr(video_config, "ASSETS_DIR", Path("assets"))
    track = (manifest.get("creative_choices") or {}).get("music_track")
    if not track:
        return None
    p = assets_dir / track
    return p if p.exists() else None


# ─────────────────────────── Helpers: Text rendering ────────────────────────── #

def _text_length(font: ImageFont.FreeTypeFont, txt: str, *, stroke_width: int = 0) -> float:
    """Return pixel width of text for the given font.
    Uses getbbox/getlength when available; falls back to a simple estimate.
    """
    if hasattr(font, "getbbox"):
        left, top, right, bottom = font.getbbox(txt, stroke_width=stroke_width)
        return right - left
    if hasattr(font, "getlength"):
        return font.getlength(txt)
    return len(txt) * font.size * 0.6


def _wrap_to_width(txt: str, font_size: int, max_width: int) -> str:
    fnt = ImageFont.truetype(str(video_config.FONT_PATH), font_size)
    if _text_length(fnt, txt) <= max_width:
        return txt
    avg_char = _text_length(fnt, "a") or (font_size * 0.5)
    width_chars = max(1, int(max_width / max(avg_char, 1)))
    wrapper = textwrap.TextWrapper(width=width_chars, break_long_words=True, replace_whitespace=False)
    return "\n".join(wrapper.wrap(txt))


def text_img(txt, font_size, color, max_allowed_width=None, stroke_width=0, stroke_fill=None):
    """Render text to a transparent RGBA PIL image."""
    fnt = ImageFont.truetype(str(video_config.FONT_PATH), font_size)
    _stroke_fill = color if stroke_fill is None else stroke_fill

    final_txt = txt
    # Optionally wrap to width
    if max_allowed_width:
        width_now = _text_length(fnt, txt, stroke_width=stroke_width)
        if width_now > max_allowed_width:
            avg_char_width = _text_length(fnt, "a") or (font_size * 0.5)
            wrap_count = max(1, int(max_allowed_width / max(avg_char_width, 1)))
            wrapper = textwrap.TextWrapper(width=wrap_count, break_long_words=True, replace_whitespace=False)
            final_txt = "\n".join(wrapper.wrap(txt))

    is_multiline = ("\n" in final_txt)

    if is_multiline:
        spacing = int(font_size * video_config.MULTILINE_SPACING_FACTOR)
        probe = Image.new("RGBA", (1, 1))
        d = ImageDraw.Draw(probe)
        left, top, right, bottom = d.multiline_textbbox((0, 0), final_txt, font=fnt, spacing=spacing, stroke_width=stroke_width)
        w, h = right - left, bottom - top
        img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.multiline_text((-left, -top), final_txt, font=fnt, fill=color, spacing=spacing,
                            stroke_width=stroke_width, stroke_fill=_stroke_fill)
    else:
        left, top, right, bottom = fnt.getbbox(final_txt, stroke_width=stroke_width)
        w, h = right - left, bottom - top
        img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((-left, -top), final_txt, font=fnt, fill=color,
                  stroke_width=stroke_width, stroke_fill=_stroke_fill)
    return img


def pil_to_clip(img, start, dur, pos=("center", "center")):
    """Convert a PIL image to a MoviePy ImageClip with timing and positioning."""
    return ImageClip(np.array(img)).with_start(start).with_duration(dur).with_position(pos)


# ───────────────────────── Typing / Signoff Clip Builders ───────────────────── #

def create_typing_animation_clip(text_to_type, base_pos, start_delay, font_size, color, speed_cps,
                                 stroke_width=0, stroke_fill=None):
    """Create a typing animation for the given text.
    Returns: (clip, final_text_pil, (canvas_w, canvas_h), (anchor_x, anchor_y)) or None
    """
    if not text_to_type:
        return None

    cursor_on_dur = 1.0 / (video_config.CURSOR_BLINK_RATE_HZ * 2)
    _stroke_fill = color if stroke_fill is None else stroke_fill

    widest_glitch = "M" * video_config.TEXT_GLITCH_MAX_AFFECTED_CHARS
    sizing_text = text_to_type + widest_glitch + video_config.CURSOR_CHAR
    canvas_pil = text_img(sizing_text, font_size, color, None, stroke_width=stroke_width, stroke_fill=_stroke_fill)
    frame_w, frame_h = canvas_pil.size

    final_text_pil = text_img(text_to_type, font_size, color, None, stroke_width=stroke_width, stroke_fill=_stroke_fill)
    final_x = (frame_w - final_text_pil.width) // 2
    final_y = (frame_h - final_text_pil.height) // 2

    flat = list(text_to_type)
    total_chars = len(text_to_type.replace("\n", ""))
    duration = total_chars / max(speed_cps, 1e-6)

    last_glitch_time = -1.0
    last_glitch_string = ""

    def make_frame(t):
        nonlocal last_glitch_time, last_glitch_string
        frame = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        num_chars = int(t * speed_cps)
        current_text = "".join(flat[:num_chars])
        render_text = current_text

        if video_config.TEXT_GLITCH_ENABLED and t < duration - (1.0 / video_config.FPS):
            if (t - last_glitch_time) >= (1.0 / video_config.TEXT_GLITCH_SPEED_HZ):
                last_glitch_string = random.choice(video_config.TEXT_GLITCH_CHAR_SET)
                last_glitch_time = t
            render_text += last_glitch_string

        show_cursor = (t < duration) and ((t % (1.0 / video_config.CURSOR_BLINK_RATE_HZ)) < cursor_on_dur)
        if show_cursor:
            if render_text.endswith("\n"):
                render_text += video_config.CURSOR_CHAR
            elif len(flat) > num_chars and flat[num_chars] == "\n":
                render_text = "".join(flat[:num_chars]) + video_config.CURSOR_CHAR + "".join(flat[num_chars:])
            else:
                render_text += video_config.CURSOR_CHAR

        txt_pil = text_img(render_text, font_size, color, None, stroke_width=stroke_width, stroke_fill=_stroke_fill)
        frame.paste(txt_pil, (final_x, final_y), txt_pil)
        return np.array(frame)

    clip = VideoClip(make_frame, duration=duration).with_start(start_delay).with_position(base_pos)
    return clip, final_text_pil, (frame_w, frame_h), (final_x, final_y)


def build_signoff_clip(palette, config):
    clips = []
    main = palette['main']
    lines_data = config.SIGNOFF_LINES

    gap = getattr(config, "SIGNOFF_GAP_S", 0.2)
    hold_tail = getattr(config, "SIGNOFF_HOLD_DURATION_S", 1.5)

    current_time = 0.0
    typed = []  # store (anim_clip, hold_img, canvas_size, anchor, y)

    for line_info in lines_data:
        text = line_info["text"]
        y_pos = line_info["y_pos"]

        res = create_typing_animation_clip(
            text,
            ("center", y_pos),
            start_delay=current_time,
            font_size=config.SIGNOFF_FONT_SIZE,
            color=main,
            speed_cps=config.SIGNOFF_TYPING_SPEED_CPS,
        )
        if not res:
            continue

        anim, hold_img, canvas_size, anchor = res
        clips.append(anim)
        typed.append((anim, hold_img, canvas_size, anchor, y_pos))

        # chain sequentially: next line starts after this one finishes + a small gap
        current_time = anim.end + gap

    if not typed:
        return None

    total_duration = current_time + hold_tail

    # keep each line visible after it finishes typing
    for anim, hold_img, canvas_size, anchor, y_pos in typed:
        padded = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        padded.paste(hold_img, anchor)
        clips.append(
            ImageClip(np.array(padded))
            .with_start(anim.end)
            .with_duration(max(0.0, total_duration - anim.end))
            .with_position(("center", y_pos))
        )

    bg = ColorClip(size=(config.W, config.H), color=palette['bg'], duration=total_duration)
    return CompositeVideoClip([bg, *clips], size=(config.W, config.H))


# ─────────────────────────── Puzzle Clip Builder ────────────────────────────── #

def build_puzzle_clip(palette, lines, index_of_anomaly, explanation, title="FIND THE ANOMALY"):
    """
    Assemble the full puzzle sequence with:
      - Title typing
      - Line typing (chained by true durations)
      - Fixed countdown starting after the last line
      - Explanation typing + hold
    """

    clips = []
    main_color = palette["main"]

    wrapped_title = _wrap_to_width(title, video_config.TITLE_FONT_SIZE, video_config.MAX_TEXT_WIDTH_PX)
    wrapped_lines = [_wrap_to_width(line, video_config.PUZZLE_LINE_FONT_SIZE, video_config.MAX_TEXT_WIDTH_PX) for line in lines]
    wrapped_expl  = _wrap_to_width(explanation.upper(), video_config.EXPLANATION_FONT_SIZE, video_config.MAX_TEXT_WIDTH_PX)

    # --- title typing ---
    current_time = 0.2
    title_res = create_typing_animation_clip(
        wrapped_title, ("center", 250), current_time,
        video_config.TITLE_FONT_SIZE, main_color, video_config.TITLE_TYPING_SPEED_CPS,
        stroke_width=video_config.TITLE_STROKE_WIDTH, stroke_fill=main_color
    )
    if not title_res:
        raise RuntimeError("Title typing clip could not be created.")
    title_anim, title_hold_img, title_canvas, title_anchor = title_res
    clips.append(title_anim)
    current_time = title_anim.end

    # --- line typing (chain by true durations) ---
    holds, ends = [], []
    y_pos = video_config.LINE_START_Y
    for i, txt in enumerate(wrapped_lines):
        res = create_typing_animation_clip(
            txt, ("center", y_pos), current_time,
            video_config.PUZZLE_LINE_FONT_SIZE, main_color, video_config.PUZZLE_TYPING_SPEED_CPS,
            stroke_width=video_config.PUZZLE_STROKE_WIDTH, stroke_fill=main_color
        )
        if res:
            anim, hold_img, canvas, anchor = res
            clips.append(anim)
            holds.append({
                "img": hold_img, "size": canvas, "anchor": anchor,
                "pos_y": y_pos, "start": anim.end, "is_anomaly": (i == index_of_anomaly)
            })
            ends.append(anim.end)
            y_pos += canvas[1] + video_config.MIN_VERTICAL_GAP_BETWEEN_PUZZLE_LINES
            current_time = anim.end

    last_line_end = max(ends) if ends else current_time

    # --- fixed countdown ---
    PRE_COUNTDOWN_PAUSE_S = getattr(video_config, "PRE_COUNTDOWN_PAUSE_S", 0.0)
    COUNTDOWN_SECONDS     = getattr(video_config, "COUNTDOWN_SECONDS", 5)

    countdown_start   = last_line_end + PRE_COUNTDOWN_PAUSE_S
    reveal_start_time = countdown_start + COUNTDOWN_SECONDS

    for i, sec in enumerate(range(COUNTDOWN_SECONDS, 0, -1)):
        num_img = text_img(str(sec), video_config.COUNTDOWN_FONT_SIZE, main_color)
        clips.append(pil_to_clip(num_img, countdown_start + i, 1.0, ("center", video_config.H - 500)))

    # --- explanation typing ---
    expl_start_time = reveal_start_time + getattr(video_config, "REVEAL_TO_EXPLANATION_DELAY_S", 0.5)
    res = create_typing_animation_clip(
        wrapped_expl, ("center", 300), expl_start_time,
        video_config.EXPLANATION_FONT_SIZE, main_color, video_config.EXPLANATION_TYPING_SPEED_CPS,
        stroke_width=video_config.PUZZLE_STROKE_WIDTH, stroke_fill=main_color
    )

    total_duration = reveal_start_time
    if res:
        expl_anim, expl_hold, expl_canvas, expl_anchor = res
        clips.append(expl_anim)
        hold_start = expl_anim.end
        hold_dur   = getattr(video_config, "EXPLANATION_HOLD_DURATION_S", 2.0)
        total_duration = hold_start + hold_dur

        padded_expl = Image.new("RGBA", expl_canvas, (0, 0, 0, 0))
        padded_expl.paste(expl_hold, expl_anchor)
        clips.append(pil_to_clip(padded_expl, hold_start, hold_dur, ("center", 300)))

    # --- keep title until reveal ---
    padded_title = Image.new("RGBA", title_canvas, (0, 0, 0, 0))
    padded_title.paste(title_hold_img, title_anchor)
    clips.append(pil_to_clip(padded_title, title_anim.end, max(0.0, reveal_start_time - title_anim.end), ("center", 250)))

    # --- keep lines visible; anomaly stays to the very end ---
    for h in holds:
        hold_end_time = total_duration if h["is_anomaly"] else reveal_start_time
        hold_dur = max(0.0, hold_end_time - h["start"])
        if hold_dur > 0.0:
            padded_line = Image.new("RGBA", h["size"], (0, 0, 0, 0))
            padded_line.paste(h["img"], h["anchor"])
            clips.append(pil_to_clip(padded_line, h["start"], hold_dur, ("center", h["pos_y"])))

    # --- compose ---
    bg = ColorClip(size=(video_config.W, video_config.H), color=palette["bg"], duration=total_duration)
    return CompositeVideoClip([bg, *clips], size=(video_config.W, video_config.H))


# ─────────────────────────────── Job Processing ─────────────────────────────── #

JOBS_DIR = video_config.JOBS_DIR


def find_unprocessed_jobs():
    """Yield job folders missing an .mp4 file."""
    if not JOBS_DIR.exists():
        return
    for job_dir in JOBS_DIR.iterdir():
        if job_dir.is_dir():
            if not any(job_dir.glob("*.mp4")) and (job_dir / "puzzle.json").exists():
                yield job_dir


def process_job(job_dir: Path):
    """Render a video for the puzzle in job_dir."""
    puzzle_file = job_dir / "puzzle.json"
    with open(puzzle_file, "r", encoding="utf-8") as f:
        puzzle = json.load(f)

    lines = puzzle.get("puzzle_lines_with_error", [])
    explanation = puzzle.get("explanation", "")
    anomaly_text = puzzle.get("text_of_erroneous_line", "")
    try:
        anomaly_index = lines.index(anomaly_text)
    except ValueError:
        anomaly_index = 0

    manifest = _load_manifest(job_dir)
    palette = _select_palette(manifest)

    # Build
    # Build title once, from manifest/puzzle
    video_title = make_video_title(manifest, puzzle, job_dir)

    puzzle_clip = build_puzzle_clip(palette, lines, anomaly_index, explanation, title=video_title)
    signoff_clip = build_signoff_clip(palette, video_config)
    final_clip = concatenate_videoclips([puzzle_clip, signoff_clip])

    # Render silent
    silent_video_path = job_dir / "temp_silent_video.mp4"
    final_clip.write_videofile(
        str(silent_video_path),
        fps=video_config.FPS,
        codec="libx264",
        audio=False,
    )
    print(f"Rendered silent: {silent_video_path}")

    # Optional: mux audio
    audio_path = _select_music(manifest)
    final_output_path = job_dir / "video.mp4"

    if audio_path and audio_path.exists():
        print(f"Using music: {audio_path.resolve()}")
        from audio_mux import mux_audio
        mux_audio(
            video_path=silent_video_path,
            audio_path=audio_path,
            output_path=final_output_path,
        )
        print(f"Muxed video: {final_output_path}")
    else:
        print("No music found in manifest/assets; saving silent video.")
        if final_output_path != silent_video_path and silent_video_path.exists():
            silent_video_path.replace(final_output_path)
    print("Marking job as rendered and updating manifest...")
    manifest['status']['video_rendered'] = True
    manifest["video_file"] = "video.mp4"
    _save_manifest(job_dir, manifest) # Use your existing function
    print(f"Manifest saved for job: {job_dir.name}")

if __name__ == "__main__":
    jobs = list(find_unprocessed_jobs())
    if not jobs:
        print("No unprocessed jobs found.")
    else:
        for job_dir in jobs:
            print(f"--- Processing job: {job_dir.name} ---")
            process_job(job_dir)
