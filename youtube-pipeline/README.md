# YouTube Video Analysis Pipeline

End-to-end pipeline that downloads YouTube videos, extracts keyframes every 15 seconds, transcribes audio with OpenAI Whisper, and generates a synced digest linking visual frames to spoken content.

## What It Does

1. **Downloads** the YouTube video and metadata via yt-dlp
2. **Extracts audio** as 16kHz mono WAV (optimized for Whisper)
3. **Extracts keyframes** every 15 seconds as PNG images
4. **Transcribes** audio using Whisper's base model
5. **Generates digest** syncing keyframe timestamps to transcript segments
6. **Builds metadata** JSON with video stats, channel info, and processing details
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
KEYFRAME_INTERVAL = 15                # Seconds between keyframes
WHISPER_MODEL = "base"                # Whisper model size
```

## Usage

```bash
# Process a YouTube video
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Process with a custom alias
python process-video.py "https://youtu.be/VIDEO_ID" --alias "conference-keynote"

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
| `keyframes/` | PNG keyframes extracted at 15-second intervals |

## Why 15-Second Intervals?

YouTube videos are typically 5-60+ minutes long. A 15-second keyframe interval balances detail against volume -- a 10-minute video produces ~40 keyframes. This captures major scene transitions and slide changes without generating hundreds of frames. For shorter YouTube content (Shorts), you may want to reduce this to 3 seconds.

## Differences from TikTok Pipeline

| Feature | TikTok Pipeline | YouTube Pipeline |
|---------|----------------|-----------------|
| Keyframe interval | 3 seconds | 15 seconds |
| Typical video length | 15-60 seconds | 5-60+ minutes |
| Video ID format | Numeric (15-25 digits) | Alphanumeric (11 chars) |
| Metadata fields | Creator, views, likes | Channel, subscribers, tags, categories |
