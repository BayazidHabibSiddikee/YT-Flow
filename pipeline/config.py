#!/usr/bin/env python3
"""Marin Video Pipeline — Central Configuration

All paths, niche definitions, API keys, and settings in one place.
Uses freellmapi backend for LLM, Kaggle GPU for Vibe Voice TTS.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
# Also try loading from pipeline dir
load_dotenv(Path(__file__).parent / ".env", override=False)

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent

# ── PATHS ────────────────────────────────────────────────────────────────────
NICHES_DIR = BASE_DIR / "niches"
COLLECTION_DIR = BASE_DIR / "collection"
OUTPUT_DIR = BASE_DIR / "output"
AUDIO_COLLECTION = COLLECTION_DIR / "audio"
IMAGES_COLLECTION = COLLECTION_DIR / "images"
VIDEO_COLLECTION = COLLECTION_DIR / "video"
SHORTS_OUTPUT = OUTPUT_DIR / "shorts"
LONGS_OUTPUT = OUTPUT_DIR / "longs"

# Assets
ASSETS_DIR = PROJECT_DIR / "assets"
ASSETS_AUDIO = ASSETS_DIR / "audio"
ASSETS_IMAGES = ASSETS_DIR / "images"
ASSETS_VIDEO = ASSETS_DIR / "video"
ASSETS_BOOKS = ASSETS_DIR / "books"

# Character
CHARACTER_DIR = PROJECT_DIR / "character"

# Tools
VIBE_VOICE_DIR = ASSETS_AUDIO / "VibeVoice"
PIPER_VOICES_DIR = ASSETS_AUDIO / "piper-voices"
MONEY_PRINTER_DIR = PROJECT_DIR / "tools" / "MoneyPrinterTurbo"
EDITOR_DIR = BASE_DIR / "editor"

# ── NICHE DEFINITIONS ────────────────────────────────────────────────────────
NICHES = {
    "izuku_midoriya": {
        "name": "Izuku Midoriya",
        "description": "Wealthy polymath — business, faith, fitness, family, psychology",
        "voice": "male_motivational",
        "edge_tts_voice": "en-US-ChristopherNeural",
        "edge_tts_rate": "+0%",
        "content_type": "both",
        "yt_channel": "",
        "character_dir": CHARACTER_DIR,
        "rag_dir": NICHES_DIR / "izuku_midoriya" / "rag" / "data",
        "templates_dir": NICHES_DIR / "izuku_midoriya" / "templates",
    },
}

# ── LLM CONFIG ───────────────────────────────────────────────────────────────
FREELLMAPI_URL = os.getenv("FREELLMAPI_URL", "http://localhost:3001")
FREELLMAPI_KEY = os.getenv("FREELLMAPI_KEY", "freellmapi-05c2b4b3bbdfadfb5b2ce3df63a132c6995b97002194718c")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "http://localhost:5071/v1")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# ── TTS CONFIG ───────────────────────────────────────────────────────────────
KAGGLE_API_TOKEN = os.getenv("KAGGLE_API_TOKEN", "")
VIBE_VOICE_MODEL = os.getenv("VIBE_VOICE_MODEL", "myshell-ai/CosyVoice-300M")

# ── VIDEO CONFIG ─────────────────────────────────────────────────────────────
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
VIDEO_RESOLUTION = (1080, 1920)  # 9:16 vertical for shorts
FPS = 30

# MiniMax H3 video generation
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.io"
MINIMAX_MODEL = "MiniMax-H3"

# ── IMAGE GENERATION ─────────────────────────────────────────────────────────
IMAGE_API = "pollinations"  # free, no key needed
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&seed={seed}&nologo=true"

# ── EDITOR ───────────────────────────────────────────────────────────────────
# Videos go to editor (opencode/claude/cline) for captions + polish
EDITOR_AI = os.getenv("EDITOR_AI", "opencode")

# ── COLLECTION LIMITS ────────────────────────────────────────────────────────
MAX_COLLECTION_AUDIO = 100
MAX_COLLECTION_IMAGES = 200
MAX_COLLECTION_VIDEO = 50
