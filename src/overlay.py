"""
Subtitle overlay - Burn subtitles onto video using FFmpeg.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def burn_subtitles(video_file: Path, srt_file: Path, output_dir: Path) -> Path:
    """
    Burn subtitles from .srt file onto video.

    Args:
        video_file: Path to input video
        srt_file: Path to .srt subtitle file
        output_dir: Directory to save output

    Returns:
        Path to video with burned subtitles
    """
    output_file = output_dir / f"{video_file.stem}_subs.mp4"

    # Skip if already exists
    if output_file.exists():
        logger.info(f"  ⚠ Subtitled video already exists: {output_file.name}")
        return output_file

    # Convert Windows path to format FFmpeg can handle
    srt_file_escaped = str(srt_file).replace("\\", "/").replace(":", r"\:")

    # FFmpeg subtitle styling
    # - FontSize=28: Large readable text
    # - OutlineColour=&H40000000&: Semi-transparent black outline
    # - BorderStyle=3: Opaque box background
    # - Alignment=2: Bottom center
    subtitle_style = (
    "FontName=Montserrat ExtraBold,"
    "FontSize=30,"
    "PrimaryColour=&HFFFFFF&,"     
    "OutlineColour=&H000000&,"     # Black border
    "BorderStyle=2,"               # No background box
    "Outline=1,"                   # Thin outline
    "Shadow=1,"                    # No shadow
    "Alignment=2,"                 # Bottom center
    "MarginV=40"                   # Padding from bottom
)



    cmd = [
        "ffmpeg",
        "-i", str(video_file),
        "-vf", f"subtitles={srt_file_escaped}:force_style='{subtitle_style}'",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",  # Copy audio without re-encoding
        "-y",
        str(output_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"FFmpeg output: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Subtitle burning failed: {e.stderr}")
        raise RuntimeError(f"Failed to burn subtitles: {e}")

    return output_file
