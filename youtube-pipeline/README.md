# YouTube Video Analysis Pipeline

End-to-end pipeline that downloads YouTube videos, extracts keyframes every 15 seconds, transcribes audio with OpenAI Whisper, and generates a synced digest linking visual frames to spoken content.

## What It Does

1. **Downloads** the YouTube video and metadata via yt-dlp
2. **Extracts audio** as 16kHz mono WAV (optimized for Whisper)
3. **Extracts keyframes** every N seconds as PNG images (default: 15)
4. **Transcribes** audio using Whisper (configurable model size)
5. **Generates digest** syncing keyframe timestamps to transcript segments
6. **Builds metadata** JSON with video stats, channel info, and processing details
7. **Updates index** JSON for tracking all processed videos

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and in PATH
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and in PATH (or set `YTDLP_PATH` env var)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Process a YouTube video
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Process with a custom alias
python process-video.py "https://youtu.be/VIDEO_ID" --alias "conference-keynote"

# Use a larger Whisper model for better accuracy
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID" --model medium

# Custom output directory and keyframe interval
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID" -o ./my-output -i 30

# Verify all tools are installed
python process-video.py --test

# Show full help
python process-video.py --help
```

## CLI Reference

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `url` | | *(required)* | YouTube video URL to process |
| `--output-dir` | `-o` | env `YOUTUBE_OUTPUT_DIR` or `./output` | Output directory |
| `--model` | `-m` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `--interval` | `-i` | `15` | Keyframe extraction interval in seconds |
| `--alias` | `-a` | auto-generated from title | Custom alias for the video |
| `--test` | | | Verify all tools are installed without processing |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `YOUTUBE_OUTPUT_DIR` | Default output directory (overridden by `--output-dir`) |
| `YTDLP_PATH` | Path to yt-dlp executable (default: `yt-dlp` in PATH) |

## Output Structure

```
output/
  index.json
  {video_id}/
    video.mp4
    audio.wav
    transcript.txt
    digest.txt
    metadata.json
    keyframes/
      frame_000s.png
      frame_015s.png
      frame_030s.png
      ...
```

## Output Files

| File | Description |
|------|-------------|
| `video.mp4` | Downloaded video |
| `audio.wav` | Extracted audio (16kHz mono) |
| `transcript.txt` | Timestamped transcription from Whisper |
| `digest.txt` | Keyframe-synced digest linking visuals to speech |
| `metadata.json` | Video metadata, stats, and processing info |
| `keyframes/` | PNG keyframes extracted at configured intervals |

## Cross-Platform Compatibility

This pipeline works on **Windows, Linux, and macOS**. A Windows UTF-8 console fix is included automatically -- no manual configuration needed. On all platforms, FFmpeg and yt-dlp must be in PATH or configured via environment variables.

## Why 15-Second Intervals?

YouTube videos are typically 5-60+ minutes long. A 15-second keyframe interval balances detail against volume -- a 10-minute video produces ~40 keyframes. This captures major scene transitions and slide changes without generating hundreds of frames. For shorter YouTube content (Shorts), reduce the interval with `--interval 3`.

## Differences from TikTok Pipeline

| Feature | TikTok Pipeline | YouTube Pipeline |
|---------|----------------|-----------------|
| Keyframe interval | 3 seconds | 15 seconds |
| Typical video length | 15-60 seconds | 5-60+ minutes |
| Video ID format | Numeric (15-25 digits) | Alphanumeric (11 chars) |
| Metadata fields | Creator, views, likes | Channel, subscribers, tags, categories |

## Troubleshooting

**yt-dlp fails to download:** YouTube frequently changes their anti-bot measures. Update yt-dlp to the latest version:
```bash
pip install -U yt-dlp
```

**First run is slow:** Whisper downloads the model on first use (~140 MB for `base`). Subsequent runs use the cached model. Larger models (`medium` ~1.5 GB, `large` ~3 GB) take longer to download and run but produce more accurate transcriptions.

**FFmpeg not found:** Ensure FFmpeg is installed and in your system PATH. Test with `ffmpeg -version`. On Windows, you can install via `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/).

**Unicode errors in video titles:** The pipeline includes automatic UTF-8 encoding fixes for Windows. If you still see encoding issues, ensure your terminal supports UTF-8 output.

**Age-restricted videos:** Some videos require authentication. You can pass cookies to yt-dlp by setting the `YTDLP_PATH` env var to a wrapper script that includes `--cookies-from-browser` flags.
