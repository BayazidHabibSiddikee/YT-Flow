# 🎬 YT-Flow Pipeline Log

> **Start here to understand what's been done.**
> Any AI working in this repo should read this file first.

---

## Videos Processed

| Date | ID | Raw File | Final File | Duration | Resolution | Status | Platforms |
|------|----|----------|------------|----------|------------|--------|-----------|
| 2026-09-08 | VID-001 | `hf_20260908_131116_...mp4` | `video1_final.mp4` | 10s → 22s | 1280×720 | ✅ Edited, Ready | TBD |
| 2026-09-08 | VID-002 | `Fitness_video_featuring_Deku_tra...mp4` | `video2_final.mp4` | 10s → 22s | 720×1280 (portrait) | ✅ Edited, Ready | TBD |

---

## Operations Log

### 2026-09-08 — Initial Processing

- **VID-001** (Business/Motivation):
  - Extended via FFmpeg loop (stream copy) from 10.04s → 22s
  - Subtitles: Business/motivation captions (no generic CTAs)
  - Font: Arial Black, 32px, white with black outline, centered
  - Output: `videos/edited/video1_final.mp4`

- **VID-002** (Gym/Fitness):
  - Extended via FFmpeg loop from 10.00s → 22s
  - Subtitles: Gym/fitness motivation captions
  - Portrait format (720×1280) — suitable for Shorts/Reels
  - Output: `videos/edited/video2_final.mp4`

---

## Subtitle Style Guide

| Element | Value |
|---------|-------|
| Font | Arial Black |
| Size | 32px |
| Color | White (`#FFFFFF`) |
| Outline | Black, 3px |
| Position | Center, 40px bottom margin |
| Tone | **Business / Gym / Motivation only** |
| ❌ Banned | "Subscribe", "Like", "Comment", generic CTAs |

---

## Face-Swap Models

**Status: ⚠️ MODELS LOST — Need Recovery**

### Last Known Models
| Model | Type | Path | Status |
|-------|------|------|--------|
| inswapper_128.onnx | ONNX (InsightFace) | `face-swap/models/` | ❌ Missing |
| simswap_224.onnx | PyTorch → ONNX | `face-swap/models/` | ❌ Missing |
| buffalo_l | Detection | `face-swap/models/` | ❌ Missing |

### Recovery Checklist
- [ ] Search local drives for `.onnx`, `.pth`, `.pt` files
- [ ] Check browser downloads history
- [ ] Search for "inswapper", "simswap", "insightface", "roop" in Downloads
- [ ] If found → copy to `face-swap/models/`
- [ ] If not found → re-download:
  - inswapper_128.onnx: `https://github.com/facefusion/facefusion-assets/releases`
  - simswap: `https://github.com/neuralchen/SimSwap`
  - buffalo_l: `pip install insightface` then copy from `~/.insightface/`

---

## Release Schedule

| Video ID | Platform | Scheduled Time | Status |
|----------|----------|----------------|--------|
| VID-001 | YouTube | TBD | ⏳ Pending |
| VID-002 | YouTube / TikTok | TBD | ⏳ Pending |

---

## Automation

- Scheduler: `scripts/schedule_release.py`
- Cron: See `config/cron_schedule.txt`
- Platform configs: `config/platforms.yml`

---

## Notes

- **Never delete `face-swap/`** — models are expensive to recover.
- Always extend videos to **≥20 seconds** before release.
- Portrait videos (720×1280) → tag for Shorts/Reels.
- Landscape (1280×720) → tag for standard YouTube.
