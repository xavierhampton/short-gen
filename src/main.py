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
from uploader import upload_to_youtube
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
        "--max-words",
        type=int,
        default=1,
        help="Maximum words per subtitle line (default: 1)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Clip duration in seconds (extracts from end of video, default: 30)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    # YouTube upload options
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the processed video to YouTube"
    )

    parser.add_argument(
        "--title",
        type=str,
        help="Video title for YouTube upload (defaults to filename)"
    )

    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Video description for YouTube upload"
    )

    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated tags for YouTube upload (e.g., 'gaming,funny,shorts')"
    )

    parser.add_argument(
        "--privacy",
        type=str,
        choices=["public", "private", "unlisted"],
        default="private",
        help="Privacy status for YouTube upload (default: private)"
    )

    parser.add_argument(
        "--credentials",
        type=str,
        default="client_secrets.json",
        help="Path to YouTube API OAuth2 credentials file (default: client_secrets.json)"
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
            # Step 1: Convert to vertical short format (extracts last N seconds)
            logger.info("  → Converting to Shorts format...")
            short_video = convert_to_short(video_file, output_dir, duration=args.duration)
            logger.info(f"  ✓ Created: {short_video.name}")

            # Step 2: Generate subtitles (unless disabled)
            if not args.no_subs:
                logger.info("  → Generating subtitles...")
                srt_file = generate_subtitles(
                    short_video,
                    model=args.model,
                    use_gpu=args.gpu,
                    max_words=args.max_words
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

            # Step 4: Upload to YouTube (if requested)
            if args.upload:
                logger.info("  → Uploading to YouTube...")

                # Parse tags if provided
                tags = None
                if args.tags:
                    tags = [tag.strip() for tag in args.tags.split(',')]

                # Use custom title or default to filename
                title = args.title if args.title else final_video.stem.replace('_', ' ').title()

                video_id = upload_to_youtube(
                    video_file=final_video,
                    title=title,
                    description=args.description,
                    tags=tags,
                    privacy_status=args.privacy,
                    credentials_file=args.credentials
                )

                if video_id:
                    logger.info(f"  ✓ Uploaded to YouTube: https://www.youtube.com/shorts/{video_id}")
                else:
                    logger.error(f"  ✗ Failed to upload to YouTube")

        except Exception as e:
            logger.error(f"✗ Failed to process {video_file.name}: {e}")
            if args.verbose:
                logger.exception(e)
            continue

    logger.info("All videos processed!")


if __name__ == "__main__":
    main()
