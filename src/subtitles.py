"""
Subtitle generation using Whisper AI.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_subtitles(video_file: Path, model: str = "small", use_gpu: bool = False) -> Path:
    """
    Generate .srt subtitles from video audio using Whisper.

    Args:
        video_file: Path to video file
        model: Whisper model size (tiny, base, small, medium, large)
        use_gpu: Whether to use GPU acceleration

    Returns:
        Path to generated .srt file
    """
    output_file = video_file.with_suffix(".srt")

    # Skip if already exists
    if output_file.exists():
        logger.info(f"  ⚠ Subtitle file already exists: {output_file.name}")
        return output_file

    try:
        # Import here to avoid loading if not needed
        from faster_whisper import WhisperModel

        # Select device
        device = "cuda" if use_gpu else "cpu"
        compute_type = "float16" if use_gpu else "int8"

        logger.debug(f"Loading Whisper model '{model}' on {device}")
        whisper_model = WhisperModel(model, device=device, compute_type=compute_type)

        # Transcribe
        logger.debug(f"Transcribing: {video_file.name}")
        segments, info = whisper_model.transcribe(
            str(video_file),
            beam_size=5,
            word_timestamps=False
        )

        logger.debug(f"Detected language: {info.language} ({info.language_probability:.2f})")

        # Write SRT file
        with open(output_file, "w", encoding="utf-8") as srt:
            for i, segment in enumerate(segments, start=1):
                # SRT format:
                # 1
                # 00:00:00,000 --> 00:00:02,000
                # Subtitle text
                #
                start_time = format_timestamp(segment.start)
                end_time = format_timestamp(segment.end)
                text = segment.text.strip()

                srt.write(f"{i}\n")
                srt.write(f"{start_time} --> {end_time}\n")
                srt.write(f"{text}\n\n")

        logger.debug(f"Wrote {i} subtitle segments")

    except ImportError:
        logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
        raise
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        raise

    return output_file


def format_timestamp(seconds: float) -> str:
    """
    Format seconds into SRT timestamp format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
