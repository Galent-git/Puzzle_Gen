"""
Audio muxing helper: attach a music track to a silent MP4 using ffmpeg.

Usage (programmatic):
    from audio_mux import mux_audio
    muxed_path = mux_audio("output\\simple_puzzle_silent.mp4", "assets\\track_A.mp3", "output\\simple_puzzle.mp4")

CLI (optional):
    python audio_mux.py -v output\\simple_puzzle_silent.mp4 -a assets\\track_A.mp3 -o output\\simple_puzzle.mp4

Requires ffmpeg available on PATH.
"""

from __future__ import annotations
import argparse
import subprocess
from pathlib import Path
from imageio_ffmpeg import get_ffmpeg_exe


def mux_audio(video_path: str | Path, audio_path: str | Path, output_path: str | Path | None = None) -> Path:
    video = Path(video_path)
    audio = Path(audio_path)
    if output_path is None:
        output = video.with_name(video.stem.replace("_silent", "") + video.suffix)
    else:
        output = Path(output_path)

    output.parent.mkdir(parents=True, exist_ok=True)

    ff = get_ffmpeg_exe()  # Use bundled ffmpeg binary from imageio-ffmpeg

    # Always loop the audio stream; -shortest will trim to the video duration
    cmd = [
        ff, "-y",
        "-i", str(video),
        "-stream_loop", "-1", "-i", str(audio),
        "-shortest",
        "-c:v", "copy",
        "-c:a", "aac",
        str(output),
    ]

    subprocess.run(cmd, check=True)

    # On success, remove the silent source video to keep the folder clean
    try:
        if video.exists() and video != output:
            video.unlink()
    except Exception:
        # Best-effort cleanup; ignore errors
        pass

    return output


def _main():
    parser = argparse.ArgumentParser(description="Mux audio track into a silent MP4 using ffmpeg")
    parser.add_argument("-v", "--video", required=True, help="Path to silent MP4 video")
    parser.add_argument("-a", "--audio", required=True, help="Path to audio file (e.g., mp3)")
    parser.add_argument("-o", "--output", default=None, help="Output MP4 path (optional)")
    args = parser.parse_args()

    out = mux_audio(args.video, args.audio, args.output)
    print(f"Muxed video written to: {out}")


if __name__ == "__main__":
    _main()

