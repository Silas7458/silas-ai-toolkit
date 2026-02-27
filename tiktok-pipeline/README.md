# TikTok Video Analysis Pipeline

End-to-end pipeline that downloads TikTok videos, extracts keyframes every 3 seconds, transcribes audio with OpenAI Whisper, and generates a synced digest linking visual frames to spoken content.

## What It Does

1. **Downloads** the TikTok video and metadata via yt-dlp
2. **Extracts audio** as 16kHz mono WAV (optimized for Whisper)
3. **Extracts keyframes** every 3 seconds as PNG images
4. **Transcribes** audio using Whisper's base model
5. **Generates digest** syncing keyframe timestamps to transcript segments
6. **Builds metadata** JSON with video stats, creator info, and processing details
7. **Updates index** JSON for tracking all processed videos

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and in PATH
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and in PATH (or set `YTDLP` path in script)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit the configuration variables at the top of `process-video.py`:

```python
BASE_DIR = Path("./output")           # Where processed videos are stored
YTDLP = "yt-dlp"                      # Path to yt-dlp executable
KEYFRAME_INTERVAL = 3                 # Seconds between keyframes
WHISPER_MODEL = "base"                # Whisper model size
```

## Usage

```bash
# Process a TikTok video
python process-video.py "https://www.tiktok.com/@user/video/1234567890"

# Process with a custom alias
python process-video.py "https://www.tiktok.com/@user/video/1234567890" --alias "cooking-tutorial"

# Verify all tools are installed
python process-video.py --test
```

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
| `keyframes/` | PNG keyframes extracted at 3-second intervals |

## Why 3-Second Intervals?

TikTok videos are typically 15-60 seconds long. A 3-second keyframe interval captures scene changes without generating excessive frames. A 30-second TikTok produces ~10 keyframes -- enough for thorough analysis without overwhelming downstream processing.
