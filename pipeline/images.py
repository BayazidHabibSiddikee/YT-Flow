#!/usr/bin/env python3
"""Pipeline Image Generation — FAL API + Pollinations fallback

FAL API (key in .env) generates high-quality images.
Pollinations.ai is free fallback.
"""

import hashlib
import json
import urllib.request
import urllib.parse
from pathlib import Path

import requests

from config import IMAGES_COLLECTION, NICHES
from image_bank import ImageBank

# FAL API from .env
import os
FAL_KEY = os.getenv("FAL_API_KEY", "")

# Image style prompts per category (used when generating fresh images)
CATEGORY_GENERATE_STYLES = {
    "business": (
        "cinematic office scene, professional business meeting, "
        "modern workspace, warm lighting, 4k quality"
    ),
    "fitness": (
        "cinematic dark gym, dramatic spotlight, intense training, "
        "sweat, iron equipment, high contrast, 4k quality"
    ),
    "spiritual": (
        "cinematic temple interior, divine golden light, "
        "incense smoke, peaceful meditation, sacred atmosphere, 4k quality"
    ),
    "family": (
        "cinematic family scene, warm home, golden hour, "
        "happy family together, cozy atmosphere, 4k quality"
    ),
    "markets": (
        "cinematic trading floor, stock charts, financial data, "
        "blue and red candles, dramatic lighting, 4k quality"
    ),
    "tech": (
        "cinematic coding scene, dark room, code on screen, "
        "keyboard typing, neon glow, 4k quality"
    ),
    "lifestyle": (
        "cinematic luxury lifestyle, city skyline sunset, "
        "premium aesthetic, warm tones, 4k quality"
    ),
}

# Topic to category mapping keywords
TOPIC_CATEGORY_MAP = {
    "business": ["business", "money", "startup", "entrepreneur", "deal", "invest", "revenue", "profit", "market", "sales", "brand", "negotiate"],
    "fitness": ["gym", "workout", "exercise", "training", "muscle", "run", "cardio", "boxing", "fight", "sport", "discipline", "body"],
    "spiritual": ["temple", "mosque", "church", "prayer", "meditation", "faith", "god", "religion", "peace", "spiritual", "bible", "quran", "gita"],
    "family": ["family", "home", "kids", "wife", "cooking", "dinner", "weekend", "outdoor", "happy", "love"],
    "markets": ["stock", "crypto", "trading", "chart", "invest", "portfolio", "economy", "inflation", "bitcoin", "finance"],
    "tech": ["coding", "python", "linux", "computer", "code", "programming", "ai", "software", "developer"],
    "lifestyle": ["success", "luxury", "car", "travel", "city", "morning", "routine", "hustle", "boss", "grind"],
}


class ImageGenerator:
    """Generate images via FAL API (paid, high quality) or Pollinations (free)."""

    def __init__(self):
        self.output_dir = IMAGES_COLLECTION
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fal_available = bool(FAL_KEY)

    def generate_fal(self, prompt: str, output_path: Path, width: int = 1080, height: int = 1920) -> Path:
        """Generate image via FAL API — high quality."""
        if not self.fal_available:
            raise RuntimeError("FAL_API_KEY not set")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use FAL's schnell model (fast, high quality)
        url = "https://fal.run/fal-ai/fast-schnell"
        headers = {
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_images": 1,
            "enable_safety_checker": False,
        }

        print(f"[FAL] Generating image...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Get image URL from response
        images = data.get("images", [])
        if not images:
            raise RuntimeError("No images returned from FAL")

        img_url = images[0].get("url", "")
        if not img_url:
            raise RuntimeError("No image URL in FAL response")

        # Download
        img_resp = requests.get(img_url, timeout=60)
        img_resp.raise_for_status()
        output_path.write_bytes(img_resp.content)
        print(f"[FAL] Done: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
        return output_path

    def generate_pollinations(self, prompt: str, output_path: Path, seed: int = 42) -> Path:
        """Generate image via Pollinations.ai — free, decent quality."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        full_prompt = f"{prompt}, ultra detailed, cinematic lighting, 4k"
        encoded = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={seed}&nologo=true"

        print(f"[Pollinations] Generating image...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
                if len(data) > 5000:
                    output_path.write_bytes(data)
                    print(f"[Pollinations] Done: {output_path.name} ({len(data)//1024}KB)")
                    return output_path
                else:
                    raise RuntimeError(f"Image too small: {len(data)} bytes")
        except Exception as e:
            raise RuntimeError(f"Pollinations failed: {e}")

    def generate(self, niche_id: str, topic: str, story_text: str = "", count: int = 5) -> list[Path]:
        """Generate images — first try image bank, then generate fresh ones."""
        niche_style = CATEGORY_GENERATE_STYLES.get("lifestyle", "cinematic dramatic scene, 4k quality")
        img_dir = self.output_dir / niche_id
        img_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Try to get topic-matched images from image bank
        bank = ImageBank()
        bank_images = bank.get_images_for_script(story_text or topic, count=count)

        if bank_images:
            print(f"[Images] Found {len(bank_images)} matching images from bank")
            return bank_images

        # Step 2: Generate fresh images using Pollinations
        print(f"[Images] No bank images found, generating fresh...")

        # Determine category from topic
        topic_lower = (topic + " " + story_text).lower()
        category = "lifestyle"  # default
        for cat, keywords in TOPIC_CATEGORY_MAP.items():
            if any(kw in topic_lower for kw in keywords):
                category = cat
                break

        style = CATEGORY_GENERATE_STYLES.get(category, niche_style)

        images = []
        for j in range(count):
            h = hashlib.md5(f"{topic}{j}".encode()).hexdigest()[:6]
            img_path = img_dir / f"scene_{h}.jpg"
            if img_path.exists() and img_path.stat().st_size > 5000:
                images.append(img_path)
                continue

            if story_text:
                paragraphs = [p.strip() for p in story_text.split("\n\n") if p.strip() and not p.startswith("#")]
                scene_desc = paragraphs[j % len(paragraphs)][:150] if paragraphs else topic
            else:
                scene_desc = topic

            prompt = f"{style}, scene: {scene_desc}"
            seed = hash(f"{topic}{j}") % 10000

            try:
                self.generate_pollinations(prompt, img_path, seed=seed)
            except Exception as e:
                print(f"  Image {j+1} failed: {e}")
                continue

            if img_path.exists():
                images.append(img_path)

        print(f"[Images] Generated {len(images)}/{count}")
        return images
