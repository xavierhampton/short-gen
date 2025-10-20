"""
Video conversion logic - Converts standard videos to YouTube Shorts format (9:16).
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_to_short(input_video: Path, output_dir: Path) -> Path:
    """
    Convert a video to YouTube Shorts format (1080x1920, vertical).

    Creates a vertical video with:
    - Blurred background (scaled and cropped to 1080x1920)
    - Centered foreground (scaled to fit within frame)

    Args:
        input_video: Path to input video file
        output_dir: Directory to save output

    Returns:
        Path to the converted video file
    """
    output_file = output_dir / f"{input_video.stem}_short.mp4"

    # Skip if already exists
    if output_file.exists():
        logger.info(f"  ⚠ Short video already exists: {output_file.name}")
        return output_file

    # FFmpeg command to create vertical short with blurred background
    # Filter breakdown:
    # [0:v] split into two streams
    # - One for blurred background (scale, crop, blur)
    # - One for main content (scale to fit)
    # Then overlay main content on blurred background

    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        "-filter_complex",
        (
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[blurred];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[scaled];"
            "[blurred][scaled]overlay=(W-w)/2:(H-h)/2"
        ),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-y",  # Overwrite output
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
        logger.error(f"FFmpeg conversion failed: {e.stderr}")
        raise RuntimeError(f"Failed to convert video: {e}")

    return output_file
