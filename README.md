# Silas AI Toolkit

**A collection of AI-powered tools and solutions built by Silas Hartsfield**

This is a growing collection of practical AI tools for document processing, video analysis, and automation. Each tool is self-contained in its own directory with its own README, requirements, and usage examples.

---

## Tools

| Tool | Description |
|------|-------------|
| [rlm-query](./rlm-query/) | Query large documents using Recursive Language Models (RLM) with Anthropic Claude. Beats context rot -- GPT-4o mini + RLM outscored full GPT-4o by 34 points on long-document benchmarks. |
| [tiktok-pipeline](./tiktok-pipeline/) | End-to-end TikTok video analysis: download, extract keyframes (every 3s), Whisper transcription, and synced digest generation. |
| [youtube-pipeline](./youtube-pipeline/) | YouTube video analysis pipeline: download, extract keyframes (every 15s for longer content), Whisper transcription, and synced digest generation. |

---

## Getting Started

Each tool has its own `requirements.txt` and `README.md`. Navigate to the tool directory and follow the setup instructions there.

**Common prerequisites:**
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) in PATH (required for video pipelines)

## License

MIT
