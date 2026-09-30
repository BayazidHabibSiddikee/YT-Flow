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

## 🧠 DirectorBrain — ML Video Director (VID-004)

**Published video:** https://www.youtube.com/watch?v=eZ7NotgOAZU
*["I Replaced My Video Editor's Brain With Machine Learning (DirectorBrain Deep Dive)"] — 18m33s, 1920×1080, YouTube ID `eZ7NotgOAZU`, published 2026-09-30.*

An ML director that replaces static routing logic in the MediaFactory pipeline.
Code lives in `~/Documents/MediaFactory/tools/director/brain/`, models + data in
`~/Documents/MediaFactory/vault/director_ml/`.

### How it works

| Stage | Component | Result |
|-------|-----------|--------|
| Feature extraction | `features.py` — content type, keywords, length, engine affinity | Deterministic, CPU-friendly, debuggable (no pixel models) |
| Engine picker | `predictor.py` + `train_eval.py` (scikit-learn) | **95.7%** accuracy on 232 rows |
| Scene ranker | `torch_ranker.py` (PyTorch) | **99.1%** train accuracy |
| Planning | `brain_core.py` / `brain_plan.py` — `direct()` → ordered tool-call plan | 6–21 ms/plan, in-process |
| Learning loop | `engine_outcomes` + `renders` tables in SQLite | Laplace-smoothed bias applied to future picks — learns without retraining |

### Dataset (legal)

232 label rows from: own render history + local Pexels cache metadata +
synthetic rule-bootstrapping. No copyrighted footage.

### Benchmark vs alternatives

Six test scripts × four systems. **Self-reported** — I wrote the benchmark.

| System | Latency/plan | Rule violations | Learns from failures | Guarantee |
|--------|--------------|-----------------|----------------------|-----------|
| **DirectorBrain** | **6–21 ms** | **0** | **Yes** (SQLite outcomes) | Plan is executor-compatible |
| Static router | 3–8 ms | 0 | No | Hardcoded rules |
| Jev (typed router) | Network round-trip | 0 | No | Valid typed output (strong for wild option spaces) |
| LLM analyzer | Seconds + API cost | 0–2 | No | Free-form reasoning |

**Caveats (kept honest in the video):** thin-sample accuracy tail; 99.1% is
*train* not held-out; the benchmark author is the system author; Jev solves a
different problem (guaranteed valid choices) and is a legitimate choice when
the option space is wild and the caller is an agent farm.

### Dogfooding

The 18.5-min video itself was directed end-to-end by DirectorBrain:
`build_deepdive.py` → per-chapter chunked TTS → per-chapter Pexels stock
(static motion enforced) → −16 LUFS mux → 154 × 8s scenes. On completion the
brain recorded its own outcome back into the DB (`learn_from_render`).

### Face-swap pipeline update

| Tool | Purpose |
|------|---------|
| `tools/faceswap/swap_multi.py` | Multi-person swap (1–2+ identities) with cross-frame identity lock via InsightFace embedding clustering — person A stays ref A, person B stays ref B |
| `tools/faceswap/auto_ig.py` | URL → yt-dlp download → swap → 9:16 IG-ready → YT-Flow queue for **manual** posting (human stays the button) |

Person detection: yes — `swap_multi.py` runs SCRFD detection on **every frame**
and clusters faces into stable identities, so multi-person videos are handled
without manual masking.

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
