#!/usr/bin/env python3
"""
TikTok Video Analysis Pipeline

Usage:
    python process-video.py <tiktok_url> [--alias <name>]
    python process-video.py --test

Pipeline steps:
    1. yt-dlp downloads video + metadata JSON
    2. FFmpeg extracts audio.wav (16kHz mono)
    3. FFmpeg extracts keyframes at 3-second intervals
    4. Whisper base model transcribes audio -> transcript.txt
    5. Digest.txt syncs keyframes to transcript segments
    6. metadata.json captures URL, creator, stats, processing info
    7. index.json updated at root
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for emoji/Unicode in video titles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === CONFIGURATION ===
# Override these with environment variables or edit directly
BASE_DIR = Path(os.environ.get("TIKTOK_OUTPUT_DIR", "./output"))
YTDLP = os.environ.get("YTDLP_PATH", "yt-dlp")
KEYFRAME_INTERVAL = 3  # seconds (TikTok videos are short)
WHISPER_MODEL = "base"
PIPELINE_VERSION = "1.0"


def run_cmd(cmd, desc="", check=True, capture=True):
    print(f"  > {desc}" if desc else f"  > {cmd[0]}")
    result = subprocess.run(
        cmd, capture_output=capture, text=True,
        check=False, encoding="utf-8", errors="replace"
    )
    if check and result.returncode != 0:
        print(f"  [FAIL] (exit {result.returncode})")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
        raise RuntimeError(f"Command failed: {' '.join(cmd[:3])}...")
    return result


def extract_video_id(url):
    """Extract TikTok video ID from URL."""
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    # Short URL or other format -- try trailing digits
    match = re.search(r'(\d{15,25})', url)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract video ID from URL: {url}")


def format_duration(seconds):
    seconds = int(seconds)
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"
    else:
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"


def step_download(url, video_dir, video_id):
    print("\n[1/5] Downloading video...")
    video_path = video_dir / "video.mp4"
    info_path = video_dir / "info.json"

    run_cmd([
        YTDLP,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "-o", str(video_path),
        url
    ], desc="Downloading with yt-dlp")

    ytdlp_info_path = video_dir / "video.info.json"
    if ytdlp_info_path.exists():
        ytdlp_info_path.replace(info_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not downloaded to {video_path}")

    info = {}
    if info_path.exists():
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)

    print(f"  [OK] Downloaded: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return info


def step_extract_audio(video_dir):
    print("\n[2/5] Extracting audio...")
    video_path = video_dir / "video.mp4"
    audio_path = video_dir / "audio.wav"

    run_cmd([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path)
    ], desc="Extracting audio (16kHz mono WAV)")

    print(f"  [OK] Audio: {audio_path.name} ({audio_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return audio_path


def step_extract_keyframes(video_dir, duration):
    print(f"\n[3/5] Extracting keyframes (every {KEYFRAME_INTERVAL}s)...")
    video_path = video_dir / "video.mp4"
    keyframes_dir = video_dir / "keyframes"
    keyframes_dir.mkdir(exist_ok=True)

    run_cmd([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"fps=1/{KEYFRAME_INTERVAL}",
        str(keyframes_dir / "frame_%03ds.png")
    ], desc=f"Extracting keyframes at 1/{KEYFRAME_INTERVAL} fps")

    frames = sorted(keyframes_dir.glob("frame_*.png"))
    renamed = []
    for i, frame in enumerate(frames):
        timestamp = i * KEYFRAME_INTERVAL
        new_name = f"frame_{timestamp:03d}s.png"
        new_path = keyframes_dir / new_name
        if frame.name != new_name:
            frame.replace(new_path)
        renamed.append(new_path)

    print(f"  [OK] Keyframes: {len(renamed)} frames extracted")
    return renamed


def step_transcribe(video_dir):
    print(f"\n[4/5] Transcribing with Whisper ({WHISPER_MODEL})...")
    audio_path = video_dir / "audio.wav"
    transcript_path = video_dir / "transcript.txt"

    import whisper
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(str(audio_path), language="en")

    segments = result.get("segments", [])
    lines = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        lines.append(f"[{start:.1f}s - {end:.1f}s] {text}")

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  [OK] Transcript: {len(segments)} segments -> {transcript_path.name}")
    return segments


def step_build_digest(video_dir, video_id, info, segments, keyframes):
    print("\n[5/5] Building digest...")
    digest_path = video_dir / "digest.txt"

    title = info.get("title", "Unknown")
    creator = info.get("creator", info.get("uploader", info.get("channel", "Unknown")))
    duration = info.get("duration", 0)

    lines = []
    lines.append(f"TIKTOK VIDEO DIGEST -- {video_id}")
    lines.append(f"Title: {title}")
    lines.append(f"Creator: {creator} | Duration: {format_duration(duration)}")
    lines.append("=" * 80)
    lines.append("")

    for i in range(len(keyframes)):
        ts_start = i * KEYFRAME_INTERVAL
        ts_end = min((i + 1) * KEYFRAME_INTERVAL, int(duration))
        frame_name = f"frame_{ts_start:03d}s"

        frame_text_parts = []
        for seg in segments:
            seg_mid = (seg["start"] + seg["end"]) / 2
            if ts_start <= seg_mid < ts_end:
                frame_text_parts.append(seg["text"].strip())

        lines.append(f"[{frame_name}.png] {ts_start}s-{ts_end}s")
        if frame_text_parts:
            combined = " ".join(frame_text_parts)
            wrapped = _wrap_text(combined, width=76, indent="  ")
            lines.append(wrapped)
        lines.append("")

    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] Digest: {digest_path.name}")
    return digest_path


def _wrap_text(text, width=76, indent="  "):
    words = text.split()
    lines = []
    current = indent
    for word in words:
        if len(current) + len(word) + 1 > width + len(indent):
            lines.append(current)
            current = indent + word
        else:
            if current == indent:
                current += word
            else:
                current += " " + word
    if current.strip():
        lines.append(current)
    return "\n".join(lines)


def build_metadata(video_dir, video_id, alias, info, keyframes, segments):
    duration = info.get("duration", 0)
    creator = info.get("creator", info.get("uploader", info.get("channel", "")))

    metadata = {
        "video_id": video_id,
        "alias": alias,
        "url": info.get("webpage_url", info.get("original_url", "")),
        "creator": creator,
        "title": info.get("title", ""),
        "description": (info.get("description", "") or "")[:500],
        "duration_seconds": int(duration),
        "duration_string": format_duration(duration),
        "resolution": f"{info.get('width', '?')}x{info.get('height', '?')}",
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "comment_count": info.get("comment_count", 0),
        "keyframe_count": len(keyframes),
        "keyframe_interval_seconds": KEYFRAME_INTERVAL,
        "transcript_segments": len(segments),
        "date_processed": datetime.now().strftime("%Y-%m-%d"),
        "whisper_model": WHISPER_MODEL,
        "pipeline_version": PIPELINE_VERSION,
    }

    meta_path = video_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  [OK] Metadata: {meta_path.name}")
    return metadata


def update_index(video_id, metadata):
    index_path = BASE_DIR / "index.json"

    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {
            "manifest_version": "1.0",
            "last_updated": "",
            "total_videos": 0,
            "videos": []
        }

    index["videos"] = [v for v in index["videos"] if v["video_id"] != video_id]

    index["videos"].append({
        "video_id": video_id,
        "alias": metadata["alias"],
        "url": metadata["url"],
        "creator": metadata["creator"],
        "title": metadata["title"],
        "duration_seconds": metadata["duration_seconds"],
        "date_processed": metadata["date_processed"],
        "path": f"{video_id}/"
    })

    index["total_videos"] = len(index["videos"])
    index["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"  [OK] Index updated: {index['total_videos']} videos total")


def cleanup_info_json(video_dir):
    info_path = video_dir / "info.json"
    if info_path.exists():
        info_path.unlink()
        print("  [OK] Cleaned up info.json")


def process_video(url, alias=None):
    print(f"\n{'='*60}")
    print(f"TIKTOK VIDEO ANALYSIS PIPELINE v{PIPELINE_VERSION}")
    print(f"{'='*60}")
    print(f"URL: {url}")

    video_id = extract_video_id(url)
    print(f"Video ID: {video_id}")

    video_dir = BASE_DIR / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    (video_dir / "keyframes").mkdir(exist_ok=True)

    info = step_download(url, video_dir, video_id)
    duration = info.get("duration", 0)
    title = info.get("title", "Unknown")
    print(f"  Title: {title}")
    print(f"  Duration: {format_duration(duration)}")

    if not alias:
        alias = re.sub(r'[^a-z0-9]+', '-', title.lower())[:50].strip('-')
    print(f"  Alias: {alias}")

    step_extract_audio(video_dir)
    keyframes = step_extract_keyframes(video_dir, duration)
    segments = step_transcribe(video_dir)
    step_build_digest(video_dir, video_id, info, segments, keyframes)
    metadata = build_metadata(video_dir, video_id, alias, info, keyframes, segments)
    update_index(video_id, metadata)
    cleanup_info_json(video_dir)

    print(f"\n{'='*60}")
    print(f"COMPLETE -- {video_id} ({alias})")
    print(f"Output: {video_dir}")
    print(f"{'='*60}")

    return video_id, metadata


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python process-video.py <tiktok_url> [--alias <name>]")
        print("  python process-video.py --test")
        sys.exit(1)

    if sys.argv[1] == "--test":
        # Quick tool check
        print("Checking tools...")
        run_cmd([YTDLP, "--version"], desc="yt-dlp")
        run_cmd(["ffmpeg", "-version"], desc="ffmpeg")
        import whisper
        print(f"  [OK] whisper loaded (model: {WHISPER_MODEL})")
        print("All tools OK.")
        sys.exit(0)

    url = sys.argv[1]
    alias = None
    if "--alias" in sys.argv:
        idx = sys.argv.index("--alias")
        if idx + 1 < len(sys.argv):
            alias = sys.argv[idx + 1]

    process_video(url, alias)


if __name__ == "__main__":
    main()
