"""
Video conversion logic - Converts standard videos to YouTube Shorts format (9:16).
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_to_short(input_video: Path, output_dir: Path, duration: int = 30) -> Path:
    """
    Convert a video to YouTube Shorts format (1080x1920, vertical).

    Creates a vertical video with:
    - Last N seconds extracted (or full video if shorter)
    - Blurred background (scaled and cropped to 1080x1920)
    - Centered foreground (scaled to fit within frame)

    Args:
        input_video: Path to input video file
        output_dir: Directory to save output
        duration: Duration in seconds to extract from end (default: 30)

    Returns:
        Path to the converted video file
    """
    output_file = output_dir / f"{input_video.stem}_short.mp4"

    # Skip if already exists
    if output_file.exists():
        logger.info(f"  ⚠ Short video already exists: {output_file.name}")
        return output_file

    # Get video duration first
    duration_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_video)
    ]

    try:
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())

        # Calculate start time (last N seconds, or 0 if video is shorter)
        start_time = max(0, total_duration - duration)

        logger.debug(f"Video duration: {total_duration:.2f}s, extracting from {start_time:.2f}s")
    except Exception as e:
        logger.warning(f"Could not determine video duration, processing full video: {e}")
        start_time = 0

    # FFmpeg command to create vertical short with blurred background
    # Filter breakdown:
    # [0:v] split into two streams
    # - One for blurred background (scale, crop, blur)
    # - One for main content (scale to fit)
    # Then overlay main content on blurred background

    cmd = [
    "ffmpeg",
    "-ss", str(start_time),  # Start from calculated position
    "-i", str(input_video),
    "-t", str(duration),  # Extract specified duration
    "-filter_complex",
    (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=2276:1280,boxblur=4[blurred];"
        "[fg]scale=1080:-1[scaled];"
        "[blurred][scaled]overlay=(W-w)/2:(H-h)/2[tmp];"
        "[tmp]crop=720:1280:(2276-720)/2:0"
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
