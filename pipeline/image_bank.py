#!/usr/bin/env python3
"""Image Bank — Categorized images for each content pillar.

Images organized by category:
- business: office, laptop, deals, handshakes, money
- fitness: gym, weights, running, fighting
- spiritual: temple, mosque, church, meditation, prayer
- family: home, cooking, kids, outdoor
- markets: charts, trading, graphs
- tech: coding, python, linux
- lifestyle: car, luxury, success

Usage:
    from image_bank import ImageBank
    bank = ImageBank()
    images = bank.get_images("business", count=3)
    images = bank.get_images_for_script("how to start a business with no money")
"""

from pathlib import Path
import hashlib

# Category keywords for matching topics to images
CATEGORY_KEYWORDS = {
    "business": [
        "business", "money", "startup", "entrepreneur", "deal", "handshake",
        "office", "laptop", "meeting", "strategy", "revenue", "profit",
        "negotiation", "brand", "marketing", "sales", "customer", "growth",
        "invest", "capital", "fund", "pitch", "work", "desk", "plan",
    ],
    "fitness": [
        "gym", "workout", "exercise", "muscle", "running", "cardio",
        "weights", "training", "sport", "football", "cricket", "boxing",
        "fight", "martial", "body", "health", "strength", "power",
        "discipline", "routine", "morning", "pushup", "squat", "deadlift",
    ],
    "spiritual": [
        "temple", "mosque", "church", "prayer", "meditation", "yoga",
        "spiritual", "god", "faith", "religion", "bible", "quran", "gita",
        "peace", "calm", "zen", "monk", "monastery", "divine", "sacred",
        "light", "golden", "incense", "candle", "lotus", "mantra",
    ],
    "family": [
        "family", "home", "kids", "children", "wife", "cooking", "dinner",
        "weekend", "outdoor", "park", "beach", "travel", "vacation",
        "love", "hug", "smile", "happy", "together", "bond", "connect",
    ],
    "markets": [
        "chart", "trading", "stock", "market", "crypto", "bitcoin",
        "finance", "invest", "portfolio", "candle", "graph", "analysis",
        "bull", "bear", "profit", "loss", "trade", "economy", "inflation",
    ],
    "tech": [
        "coding", "python", "linux", "computer", "code", "programming",
        "developer", "software", "terminal", "keyboard", "screen",
        "robot", "ai", "machine", "data", "server", "network",
    ],
    "lifestyle": [
        "car", "luxury", "success", "watch", "travel", "city",
        "night", "sunset", "skyline", "coffee", "morning", "routine",
        "aesthetic", "vibe", "mood", "grind", "hustle", "boss",
    ],
}


class ImageBank:
    """Categorized image manager."""

    def __init__(self, bank_dir: Path = None):
        if bank_dir is None:
            bank_dir = Path("assets/images/bank")
        self.bank_dir = bank_dir
        self.bank_dir.mkdir(parents=True, exist_ok=True)

        # Create category subdirectories
        for cat in CATEGORY_KEYWORDS:
            (self.bank_dir / cat).mkdir(exist_ok=True)

    def get_images(self, category: str, count: int = 3) -> list[Path]:
        """Get images for a category from the bank."""
        cat_dir = self.bank_dir / category
        if not cat_dir.exists():
            return []

        images = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.png"))
        if not images:
            return []

        # Cycle through images if we need more than available
        result = []
        for i in range(count):
            result.append(images[i % len(images)])
        return result

    def get_images_for_script(self, script_text: str, count: int = 5) -> list[Path]:
        """Automatically match script content to image categories."""
        text_lower = script_text.lower()

        # Score each category
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = score

        # Sort by score, get top categories
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Get images from top categories
        images = []
        for cat, score in sorted_cats:
            if score > 0:
                cat_images = self.get_images(cat, count=max(1, count - len(images)))
                images.extend(cat_images)
                if len(images) >= count:
                    break

        # If no matches, get generic lifestyle images
        if not images:
            images = self.get_images("lifestyle", count)

        return images[:count]

    def scan_bank(self) -> dict:
        """Scan bank and return counts per category."""
        counts = {}
        for cat in CATEGORY_KEYWORDS:
            cat_dir = self.bank_dir / cat
            if cat_dir.exists():
                images = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.png"))
                counts[cat] = len(images)
            else:
                counts[cat] = 0
        return counts
