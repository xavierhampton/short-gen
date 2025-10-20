#!/usr/bin/env python3
"""
shortgen CLI - Main entry point for the video conversion tool.
"""

import argparse
import logging
import sys
from pathlib import Path

from converter import convert_to_short
from subtitles import generate_subtitles
from overlay import burn_subtitles
from utils import setup_logging, get_video_files


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert videos to YouTube Shorts format with automatic subtitles"
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input video file or directory containing videos"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory (default: output/)"
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=["tiny", "base", "small", "medium", "large"],
        default="small",
        help="Whisper model size (default: small)"
    )

    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU acceleration for Whisper"
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep intermediate files (vertical video, .srt)"
    )

    parser.add_argument(
        "--no-subs",
        action="store_true",
        help="Skip subtitle generation"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Get input path
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get video files to process
    if input_path.is_file():
        video_files = [input_path]
    elif input_path.is_dir():
        video_files = get_video_files(input_path)
    else:
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    if not video_files:
        logger.error("No video files found to process")
        sys.exit(1)

    logger.info(f"Found {len(video_files)} video(s) to process")

    # Process each video
    for video_file in video_files:
        logger.info(f"Processing: {video_file.name}")

        try:
            # Step 1: Convert to vertical short format
            logger.info("  → Converting to Shorts format...")
            short_video = convert_to_short(video_file, output_dir)
            logger.info(f"  ✓ Created: {short_video.name}")

            # Step 2: Generate subtitles (unless disabled)
            if not args.no_subs:
                logger.info("  → Generating subtitles...")
                srt_file = generate_subtitles(
                    short_video,
                    model=args.model,
                    use_gpu=args.gpu
                )
                logger.info(f"  ✓ Created: {srt_file.name}")

                # Step 3: Burn subtitles onto video
                logger.info("  → Burning subtitles...")
                final_video = burn_subtitles(short_video, srt_file, output_dir)
                logger.info(f"  ✓ Created: {final_video.name}")

                # Cleanup intermediate files if requested
                if not args.keep_temp:
                    logger.debug("  → Cleaning up intermediate files...")
                    short_video.unlink()
                    srt_file.unlink()
            else:
                final_video = short_video

            logger.info(f"✓ Completed: {final_video}")

        except Exception as e:
            logger.error(f"✗ Failed to process {video_file.name}: {e}")
            if args.verbose:
                logger.exception(e)
            continue

    logger.info("All videos processed!")


if __name__ == "__main__":
    main()
