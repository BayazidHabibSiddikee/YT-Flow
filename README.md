# 🎬 YT-Flow — Video Production & Release Pipeline

> **All video production, editing, face-swap tracking, and release scheduling lives here.**

YT-Flow is the single source of truth for video creation, editing, subtitle generation, face-swap model management, and multi-platform release scheduling.

---

## 📁 Directory Structure

```
YT-Flow/
├── videos/
│   ├── raw/              # Original unedited footage
│   ├── edited/           # Final cut videos ready for release
│   └── thumbnails/       # Generated thumbnails
├── subtitles/            # SRT/VTT files
├── face-swap/
│   ├── models/           # Face-swap model weights (InsightFace, SimSwap, etc.)
│   ├── references/       # Reference face images
│   └── output/           # Swapped output files
├── scripts/              # Automation scripts (edit, upload, schedule)
├── logs/                 # Pipeline execution logs
├── config/               # Platform credentials, schedule config
└── docs/                 # Guides and references
```

---

## 🚀 Quick Start

### Process a new video
```bash
python3 scripts/process_video.py --input path/to/video.mp4 --extend-to 22 --subtitles "auto"
```

### Schedule a release
```bash
python3 scripts/schedule_release.py --video edited_videos/video1_final.mp4 --platform youtube --time "2026-09-10T14:00:00"
```

### Check pipeline status
```bash
cat logs/pipeline_log.md
```

---

## 🤖 AI Collaboration

Any AI working in this environment should:
1. **Read `logs/pipeline_log.md`** first to understand what's been done
2. **Check `face-swap/models/`** for available face-swap models before requesting new ones
3. **Update `logs/pipeline_log.md`** after any video processing work
4. **Never delete files in `face-swap/`** — these are hard to recover

---

## 📋 Pipeline Steps

1. **Ingest** → Place raw footage in `videos/raw/`
2. **Analyze** → Inspect duration, codec, resolution
3. **Edit** → Extend duration, add transitions
4. **Transcribe** → Generate subtitles via Whisper
5. **Burn-in** → Embed styled captions
6. **Face-swap** (optional) → Apply face replacement if needed
7. **Thumbnail** → Generate or select thumbnail
8. **Schedule** → Add to release queue
9. **Release** → Post to platform(s) at scheduled time

---

## 🔧 Required Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `ffmpeg` | Video editing | `sudo pacman -S ffmpeg` |
| `ffprobe` | Video analysis | (bundled with ffmpeg) |
| `openai-whisper` | Transcription | `pip install openai-whisper` |
| `insightface` | Face analysis | `pip install insightface onnxruntime` |
| `python3` | Scripting | (system) |

---

## 📝 Pipeline Log

See [`logs/pipeline_log.md`](logs/pipeline_log.md) for the full history of processed videos, edits, releases, and notes.

---

## ⚠️ Important Notes

- **Face-swap models are tracked in git** — DO NOT lose these. They take hours to train/collect.
- All releases are logged with platform, timestamp, and performance metrics.
- The `config/` directory contains sensitive data (API keys) and is gitignored.
