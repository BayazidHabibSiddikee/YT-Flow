# Marin Video Pipeline

**Goal:** Automated story/advice video generation — YouTube Shorts and long-form content across 3 niches, powered by LangChain + RAG + Kaggle Vibe Voice + FFmpeg.

**Revenue:** YouTube ad revenue from niche content channels.

---

## Pipeline Flow

```
GENERATE → RAG + LangChain → story/advice text
    ↓
TTS → Kaggle Vibe Voice (CosyVoice) → .mp3
    ↓ (fallback: edge-tts)
IMAGES → Pollinations AI → scene images
    ↓
VIDEO → FFmpeg → shorts (9:16) or longs (16:9)
    ↓
EDITOR → opencode/claude/cline → captions + polish
    ↓
OUTPUT → ready to post
```

## Niches

| # | Niche | Voice | Content |
|---|-------|-------|---------|
| 1 | Izuku Midoriya (war stories) | Old man (slow, deep) | Shorts |
| 2 | Gym Mentality (discipline/ego) | Male motivational | Shorts + Longs |
| 3 | Krishna Religious (spiritual) | Female calm | Shorts + Longs |
| 4 | *Later* | *TBD* | *TBD* |

## Quick Start

```bash
cd ~/Documents/socio_business/pipeline

# Index RAG knowledge bases
python pipeline.py index

# Generate short
python pipeline.py short izuku_midoriya "the night before the battle"

# Generate long
python pipeline.py long gym_mentality "why ego kills progress"

# Download YouTube content for RAG
python pipeline.py download "https://youtube.com/watch?v=..." izuku_midoriya

# Check status
python pipeline.py status
```

## Directory Structure

```
pipeline/
├── config.py              # All settings, paths, niche definitions
├── pipeline.py            # Main orchestrator (CLI)
├── generator.py           # LangChain story generator
├── tts.py                 # Kaggle Vibe Voice + edge-tts
├── video_combiner.py      # FFmpeg video creation
├── youtube_downloader.py  # yt-dlp downloader
├── .env                   # API keys (in parent dir)
│
├── rag/
│   └── rag_engine.py      # FAISS + HuggingFace RAG
│
├── niches/
│   ├── izuku_midoriya/    # Old war vet stories
│   │   ├── rag/data/      # War books, memoirs
│   │   └── templates/
│   ├── gym_mentality/     # Discipline/ego advice
│   │   ├── rag/data/      # Stoic/psychology texts
│   │   └── templates/
│   └── krishna_religious/ # Spiritual wisdom
│       ├── rag/data/      # Religious texts
│       └── templates/
│
├── collection/            # Assets staging
│   ├── audio/
│   ├── images/
│   └── video/
│
├── output/                # Generated videos
│   ├── shorts/
│   └── longs/
│
└── editor/
    └── editor.py          # AI video editor
```

## Adding Knowledge to RAG

Drop files into `niches/<name>/rag/data/`:
```
niches/izuku_midoriya/rag/data/
├── war_stories.pdf
├── military_history.txt
└── personal_memories.md
```

Then re-index: `python pipeline.py index`

## Integrations

- **LLM Backend:** freellmapi (localhost:3001) → OpenRouter → Ollama
- **TTS:** Kaggle GPU CosyVoice → edge-tts fallback
- **Images:** Pollinations AI (free, no key)
- **Video:** FFmpeg (local)
- **Editor:** opencode/claude/cline with bypass permission
- **YouTube:** yt-dlp for content collection

## API Keys (in parent .env)

Already configured:
- `FREELLMAPI_KEY` — LLM backend
- `KAGGLE_API_TOKEN` — GPU TTS
- `FAL_API_KEY` — image generation (if needed)

## Dependencies (already installed)

- langchain, langchain-openai, langchain-huggingface
- faiss-cpu, sentence-transformers
- yt-dlp, ffmpeg, edge-tts
- kaggle CLI
