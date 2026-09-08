# Socio Business — AI Video Content Pipeline

**Goal:** Automated YouTube content generation — AI characters, TTS, images, video, all orchestrated by LangChain + RAG + FFmpeg.

**Revenue:** YouTube ad revenue from niche content channels.

---

## Setup

```bash
cd ~/Documents/socio_business

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Install heavy packages (optional, for sentence-transformers / video)
pip install sentence-transformers faster-whisper moviepy
```

All API keys are in `.env` at project root.

---

## Project Structure

```
socio_business/
├── .env                    # API keys (FREELLMAPI, KAGGLE, FAL, etc.)
├── README.md               # This file
│
├── character/              # AI character definitions
│   ├── izuku_midoriya.md   # Main character — business, faith, fitness, family
│   ├── faces/              # Face reference images for swapping
│   ├── profiles/           # Extended character bios
│   └── templates/          # Reusable prompt templates
│
├── assets/                 # All media assets
│   ├── audio/              # TTS tools + generated audio
│   │   ├── piper-voices/   # Piper TTS voice models
│   │   ├── VibeVoice/      # Kaggle CosyVoice TTS
│   │   ├── vibevoice.cpp/  # C++ VibeVoice implementation
│   │   └── generated/      # TTS output files
│   ├── images/             # All images
│   │   ├── character/      # Character face references
│   │   ├── generated/      # AI-generated images
│   │   └── reference/      # Reference material
│   ├── video/              # All videos
│   │   ├── raw/            # Original/source videos
│   │   ├── processed/      # Face-swapped, edited
│   │   └── output/         # Final videos
│   └── books/              # PDFs/texts for RAG knowledge
│
├── pipeline/               # Core video generation engine
│   ├── config.py           # All settings, paths, niche definitions
│   ├── orchestrator.py     # Multi-agent pipeline (main entry point)
│   ├── pipeline.py         # Single-run pipeline (CLI)
│   ├── generator.py        # LangChain story generator (Izuku)
│   ├── tts.py              # Kaggle Vibe Voice + edge-tts
│   ├── images.py           # Pollinations AI image generation
│   ├── video_combiner.py   # FFmpeg video creation
│   ├── short_maker.py      # Short-form video builder
│   ├── youtube_downloader.py
│   ├── agents/             # Multi-agent system
│   │   ├── director.py     # Reviews and approves content
│   │   ├── quality_checker.py # Rates finished videos
│   │   ├── publisher.py    # YouTube + social upload
│   │   └── social_writer.py # Izuku writes social posts
│   ├── rag/                # FAISS + HuggingFace RAG engine
│   ├── niches/             # Per-niche RAG data and templates
│   ├── collection/         # Staging area for assets
│   ├── output/             # Generated videos, captions, posts
│   └── director/           # AI video editing instructions
│
├── scripts/                # Standalone utility scripts
│   ├── face_swap.py        # Face swapping tools
│   ├── yt_upload.py        # YouTube upload
│   ├── yt_token.py         # YouTube auth
│   └── generate.py         # Content generation helpers
│
├── channels/               # Channel-specific content & RAG data
│   ├── izuku_midoriya/     # Izuku Midoriya channel content
│   └── 48laws/             # 48 Laws of Power channel
│
└── tools/                  # External tools (large, gitignored)
    ├── editor/             # Video editor (JS/TS)
    ├── MoneyPrinterTurbo/  # Video automation tool
    └── dramaclaw/          # Content creation tool
```

## Pipeline Flow (Multi-Agent)

```
User Request / Poke
       ↓
  IZUKU (Generator) ──→ Creates content idea + draft text
       ↓
  DIRECTOR ──→ Reviews, approves/revolves, gives direction
       ↓
  VIDEO PRODUCER ──→ TTS + Images + FFmpeg video
       ↓
  QUALITY CHECKER ──→ Rates video 1-10, PUBLISH/EDIT/REJECT
       ↓
  PUBLISHER ──→ YouTube metadata + upload prep
       ↓
  IZUKU (Social Writer) ──→ Instagram, Twitter, TikTok, LinkedIn posts
       ↓
  OUTPUT ──→ video + captions + social posts (ready to publish)
```

### Usage

```bash
cd ~/Documents/socio_business/pipeline
source ../venv/bin/activate

# Run full pipeline
python orchestrator.py run "how to start a business with no money"

# Run with specific type
python orchestrator.py run "discipline over motivation" --type short

# Batch mode (one topic per line in file)
python orchestrator.py batch topics.txt

# Check status
python orchestrator.py status
```

### Agents

| Agent | Role | File |
|-------|------|------|
| Izuku (Generator) | Creates content from RAG + character knowledge | `generator.py` |
| Director | Reviews ideas, scores virality, gives direction | `agents/director.py` |
| Quality Checker | Rates finished videos on 5 criteria | `agents/quality_checker.py` |
| Publisher | Prepares YouTube + social upload metadata | `agents/publisher.py` |
| Izuku (Social Writer) | Writes platform-specific posts | `agents/social_writer.py` |
| Orchestrator | Ties all agents together | `orchestrator.py` |

## Characters

| Character | Content Pillars | Voice | Status |
|-----------|----------------|-------|--------|
| Izuku Midoriya | Business, Spirituality, Psychology, Fitness, Family | Male motivational | Active |

See `character/izuku_midoriya.md` for full system prompt and rules.

## Quick Start

```bash
cd ~/Documents/socio_business

# Index RAG knowledge bases
python pipeline/pipeline.py index

# Generate short
python pipeline/pipeline.py short izuku_midoriya "business mindset"

# Generate long
python pipeline/pipeline.py long izuku_midoriya "discipline over motivation"

# Download YouTube content for RAG
python pipeline/pipeline.py download "https://youtube.com/watch?v=..." izuku_midoriya

# Check status
python pipeline/pipeline.py status
```

## Integrations

- **LLM Backend:** freellmapi (localhost:3001) → OpenRouter → Ollama
- **TTS:** Kaggle GPU CosyVoice → edge-tts fallback
- **Images:** Pollinations AI (free, no key) → FAL API (premium)
- **Video:** FFmpeg (local)
- **Editor:** opencode/claude/cline with bypass permission
- **YouTube:** yt-dlp for content collection, yt-upload for publishing

## API Keys (in .env)

```
FREELLMAPI_KEY=...     # LLM backend
KAGGLE_API_TOKEN=...   # GPU TTS
FAL_API_KEY=...        # Image generation (optional)
MINIMAX_API_KEY=...    # Video generation (optional)
```

## Adding a New Character

1. Copy `character/templates/story_short.md`
2. Fill in system prompt, voice, image style, rules
3. Add face images to `character/faces/`
4. Add extended profile to `character/profiles/`
5. Create niche RAG directory in `pipeline/niches/`
6. Register in `pipeline/config.py`

## Adding RAG Knowledge

Drop files into `pipeline/niches/<name>/rag/data/`:
```
pipeline/niches/izuku_midoriya/rag/data/
├── business_books.pdf
├── psychology_texts.txt
└── spiritual_wisdom.md
```

Then re-index: `python pipeline/pipeline.py index`
