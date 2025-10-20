"""
Utility functions for Shortify.
"""

import logging
from pathlib import Path
from typing import List


# Supported video extensions
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm", ".m4v"}


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable debug-level logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def get_video_files(directory: Path) -> List[Path]:
    """
    Get all video files from a directory.

    Args:
        directory: Directory to search

    Returns:
        List of video file paths
    """
    video_files = []

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(file_path)

    # Sort alphabetically
    video_files.sort()

    return video_files
