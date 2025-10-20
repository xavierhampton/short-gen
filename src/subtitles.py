"""
Subtitle generation using Whisper AI.
"""

import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def split_into_chunks(words: List, max_words: int = 5) -> List[Dict]:
    """
    Split word-level timestamps into smaller chunks for snappier subtitles.

    Args:
        words: List of word objects with start, end, and text attributes
        max_words: Maximum words per subtitle chunk

    Returns:
        List of subtitle chunks with start, end, and text
    """
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)

        # Create chunk when we hit max words or at natural breaks
        if len(current_chunk) >= max_words:
            chunks.append({
                'start': current_chunk[0].start,
                'end': current_chunk[-1].end,
                'text': ' '.join(w.word.strip() for w in current_chunk)
            })
            current_chunk = []

    # Add remaining words as final chunk
    if current_chunk:
        chunks.append({
            'start': current_chunk[0].start,
            'end': current_chunk[-1].end,
            'text': ' '.join(w.word.strip() for w in current_chunk)
        })

    return chunks


def generate_subtitles(video_file: Path, model: str = "small", use_gpu: bool = False, max_words: int = 5) -> Path:
    """
    Generate .srt subtitles from video audio using Whisper.

    Args:
        video_file: Path to video file
        model: Whisper model size (tiny, base, small, medium, large)
        use_gpu: Whether to use GPU acceleration
        max_words: Maximum words per subtitle line

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

        # Transcribe with word-level timestamps for better chunking
        logger.debug(f"Transcribing: {video_file.name}")
        segments, info = whisper_model.transcribe(
            str(video_file),
            beam_size=5,
            word_timestamps=True  # Enable word timestamps for snappier subtitles
        )

        logger.debug(f"Detected language: {info.language} ({info.language_probability:.2f})")

        # Process segments into shorter, snappier subtitles
        subtitle_chunks = []
        for segment in segments:
            if hasattr(segment, 'words') and segment.words:
                # Split by words with configurable max words per subtitle
                chunks = split_into_chunks(segment.words, max_words=max_words)
                subtitle_chunks.extend(chunks)
            else:
                # Fallback: split by length if no word timestamps
                text = segment.text.strip()
                if len(text.split()) > max_words:
                    # Split long text into smaller chunks
                    words = text.split()
                    duration = segment.end - segment.start
                    time_per_word = duration / len(words)

                    for i in range(0, len(words), max_words):
                        chunk_words = words[i:i+max_words]
                        chunk_start = segment.start + (i * time_per_word)
                        chunk_end = segment.start + ((i + len(chunk_words)) * time_per_word)
                        subtitle_chunks.append({
                            'start': chunk_start,
                            'end': chunk_end,
                            'text': ' '.join(chunk_words)
                        })
                else:
                    subtitle_chunks.append({
                        'start': segment.start,
                        'end': segment.end,
                        'text': text
                    })

        # Write SRT file
        with open(output_file, "w", encoding="utf-8") as srt:
            for i, chunk in enumerate(subtitle_chunks, start=1):
                start_time = format_timestamp(chunk['start'])
                end_time = format_timestamp(chunk['end'])
                text = chunk['text']

                srt.write(f"{i}\n")
                srt.write(f"{start_time} --> {end_time}\n")
                srt.write(f"{text}\n\n")

        logger.debug(f"Wrote {len(subtitle_chunks)} subtitle segments")

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
