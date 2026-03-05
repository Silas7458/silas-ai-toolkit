# TikTok Video Analysis Pipeline

End-to-end pipeline that downloads TikTok videos, extracts keyframes every 3 seconds, transcribes audio with OpenAI Whisper, and generates a synced digest linking visual frames to spoken content.

## What It Does

1. **Downloads** the TikTok video and metadata via yt-dlp
2. **Extracts audio** as 16kHz mono WAV (optimized for Whisper)
3. **Extracts keyframes** every N seconds as PNG images (default: 3)
4. **Transcribes** audio using Whisper (configurable model size)
5. **Generates digest** syncing keyframe timestamps to transcript segments
6. **Builds metadata** JSON with video stats, creator info, and processing details
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
# Process a TikTok video
python process-video.py "https://www.tiktok.com/@user/video/1234567890"

# Process with a custom alias
python process-video.py "https://www.tiktok.com/@user/video/1234567890" --alias "cooking-tutorial"

# Use a larger Whisper model for better accuracy
python process-video.py "https://www.tiktok.com/@user/video/1234567890" --model medium

# Custom output directory and keyframe interval
python process-video.py "https://www.tiktok.com/@user/video/1234567890" -o ./my-output -i 5

# Verify all tools are installed
python process-video.py --test

# Show full help
python process-video.py --help
```

## CLI Reference

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `url` | | *(required)* | TikTok video URL to process |
| `--output-dir` | `-o` | env `TIKTOK_OUTPUT_DIR` or `./output` | Output directory |
| `--model` | `-m` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `--interval` | `-i` | `3` | Keyframe extraction interval in seconds |
| `--alias` | `-a` | auto-generated from title | Custom alias for the video |
| `--test` | | | Verify all tools are installed without processing |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TIKTOK_OUTPUT_DIR` | Default output directory (overridden by `--output-dir`) |
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
      frame_003s.png
      frame_006s.png
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

## Why 3-Second Intervals?

TikTok videos are typically 15-60 seconds long. A 3-second keyframe interval captures scene changes without generating excessive frames. A 30-second TikTok produces ~10 keyframes -- enough for thorough analysis without overwhelming downstream processing. Adjust with `--interval` if needed.

## Troubleshooting

**yt-dlp fails to download:** TikTok frequently changes their anti-bot measures. Update yt-dlp to the latest version:
```bash
pip install -U yt-dlp
```

**First run is slow:** Whisper downloads the model on first use (~140 MB for `base`). Subsequent runs use the cached model. Larger models (`medium` ~1.5 GB, `large` ~3 GB) take longer to download and run but produce more accurate transcriptions.

**FFmpeg not found:** Ensure FFmpeg is installed and in your system PATH. Test with `ffmpeg -version`. On Windows, you can install via `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/).

**Unicode errors in video titles:** The pipeline includes automatic UTF-8 encoding fixes for Windows. If you still see encoding issues, ensure your terminal supports UTF-8 output.
