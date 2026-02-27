# Playbook: Video Analysis Pipelines

## Overview

These pipelines download videos, extract timestamped keyframes, transcribe audio with Whisper, and generate synchronized digests. They work with TikTok and YouTube but the pattern applies to any video source.

---

## TikTok Pipeline

**Purpose:** Analyze short-form video content (typically 15s-3min).

### Quick Start
```bash
python process-video.py <TIKTOK_URL> [--alias <name>]
```

### What It Does
1. Downloads video via `yt-dlp`
2. Extracts timestamped keyframes every 3 seconds via FFmpeg
3. Runs Whisper (base model) transcription on audio
4. Syncs keyframes to transcript segments into a readable digest

### Useful Flags
- `--interval 2` -- denser keyframes (default 3s)
- `--model medium` -- better transcription accuracy (default base)
- `--skip-download` -- reprocess without re-downloading
- `--skip-transcribe` -- regenerate digest from existing transcript

### Prerequisites
- `pip install yt-dlp openai-whisper`
- FFmpeg in PATH

### Output Structure
```
{video_id}/
  video.mp4
  keyframes/
    frame_0000_00s.jpg
    frame_0001_03s.jpg
    ...
  transcript.txt
  digest_readable.txt
```

---

## YouTube Pipeline

**Purpose:** Analyze long-form video content (typically 5min-2hr).

### Quick Start
```bash
python process-video.py <YOUTUBE_URL> [--alias <name>]
```

### Differences from TikTok
- Keyframe interval: **15 seconds** (videos are longer, 3s would produce too many frames)
- Suitable for lectures, tutorials, interviews, and other long-form content

### Output Structure
Same as TikTok but with sparser keyframes.

---

## Team Research Workflow

When a research task would benefit from video content:

1. **Search for relevant videos** -- evaluate titles, descriptions, view counts, pick the best 3-5
2. **Process each video** through the pipeline -- download, keyframes, Whisper, digest
3. **Check the index first** (`index.json`) -- avoid reprocessing videos already cached
4. **Read the digest** -- `digest_readable.txt` gives you the full content without watching
5. **Synthesize and report** -- combine insights from multiple videos

### Parallel Processing
For bulk analysis, process multiple videos simultaneously:
```bash
# Process 3 videos in parallel
python process-video.py URL1 --alias "video1" &
python process-video.py URL2 --alias "video2" &
python process-video.py URL3 --alias "video3" &
wait
```

### Index Management
Each pipeline maintains an `index.json` at its root:
```json
{
  "video_id_123": {
    "alias": "human-friendly-name",
    "url": "https://...",
    "processed_at": "2026-02-23T10:30:00Z",
    "has_transcript": true,
    "has_digest": true
  }
}
```
Check this before processing to avoid duplicate work.

---

## Tips

- **Whisper model selection:** `base` is fast but less accurate. `medium` is a good balance. `large` is slow but most accurate. For most content, `base` is sufficient.
- **Keyframe interval tuning:** Dense intervals (2-3s) for fast-moving content. Sparse intervals (15-30s) for talking-head content.
- **Storage:** Video files are large. Consider deleting the source `.mp4` after processing if you only need the keyframes and transcript.
- **Rate limiting:** yt-dlp may get rate-limited by platforms. Space out bulk downloads or use `--sleep-interval` flag.

---

*This playbook covers the general pattern. Adapt paths and scripts to your own setup.*
