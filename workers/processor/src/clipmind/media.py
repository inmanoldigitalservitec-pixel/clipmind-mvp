from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def extract_audio(video_path: str | Path, output_path: str | Path, sample_rate: int = 16000) -> Path:
    video = Path(video_path)
    output = Path(output_path)

    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg was not found. Install ffmpeg before extracting audio.")

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        str(output),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed while extracting audio")

    return output
