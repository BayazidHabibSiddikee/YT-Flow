#!/usr/bin/env python3
"""Download free images for the image bank.

Sources:
- Unsplash (https://unsplash.com/) — free, high quality, no API key needed
- Pexels (https://www.pexels.com/) — free, good quality
- Pixabay (https://pixabay.com/) — free, decent quality

Usage:
    python download_images.py business "office meeting" 5
    python download_images.py fitness "gym workout" 5
    python download_images.py spiritual "temple meditation" 5
    python download_images.py all  # download starter set for all categories
"""

import sys
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

BANK_DIR = Path("assets/images/bank")

# Starter search terms per category
STARTER_QUERIES = {
    "business": [
        "business meeting modern office",
        "entrepreneur working laptop",
        "handshake deal close up",
        "money cash investment",
        "startup team strategy",
    ],
    "fitness": [
        "gym workout weights",
        "morning run sunrise",
        "boxing training fight",
        "muscular man exercise",
        "football soccer training",
    ],
    "spiritual": [
        "temple golden light",
        "meditation peaceful zen",
        "mosque architecture beautiful",
        "prayer candle spiritual",
        "bible pages faith",
    ],
    "family": [
        "family dinner together",
        "father kids playing",
        "couple cooking kitchen",
        "family outdoor adventure",
        "happy family sunset",
    ],
    "markets": [
        "stock market chart trading",
        "cryptocurrency bitcoin",
        "financial analysis graph",
        "investment portfolio",
        "business finance growth",
    ],
    "tech": [
        "coding python screen",
        "linux terminal computer",
        "developer workspace setup",
        "artificial intelligence robot",
        "data server room",
    ],
    "lifestyle": [
        "luxury car night city",
        "morning coffee routine",
        "success man watch",
        "city skyline sunset",
        "aesthetic workspace minimal",
    ],
}


def download_unsplash(query: str, output_path: Path, width: int = 1080, height: int = 1920) -> bool:
    """Download from Unsplash source (no API key needed)."""
    encoded = urllib.parse.quote(query)
    url = f"https://source.unsplash.com/{width}x{height}/?{encoded}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) > 5000:
                output_path.write_bytes(data)
                print(f"  Downloaded: {output_path.name} ({len(data)//1024}KB)")
                return True
    except Exception as e:
        print(f"  Unsplash failed: {e}")
    return False


def download_pexels(query: str, output_path: Path) -> bool:
    """Download from Pexels (free, no API key for direct URLs)."""
    # Pexels search URL — we scrape the first result
    encoded = urllib.parse.quote(query)
    url = f"https://www.pexels.com/search/{encoded}/"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode()
            # Find image URL in response
            import re
            img_match = re.search(r'https://images\.pexels\.com/photos/[^"]+\.jpeg', html)
            if img_match:
                img_url = img_match.group(0)
                img_resp = urllib.request.urlopen(img_url, timeout=30)
                data = img_resp.read()
                if len(data) > 5000:
                    output_path.write_bytes(data)
                    print(f"  Downloaded: {output_path.name} ({len(data)//1024}KB)")
                    return True
    except Exception as e:
        print(f"  Pexels failed: {e}")
    return False


def download_category(category: str, queries: list[str], count_per_query: int = 1):
    """Download images for a category."""
    cat_dir = BANK_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*40}")
    print(f"  Category: {category}")
    print(f"{'='*40}")

    downloaded = 0
    for i, query in enumerate(queries):
        for j in range(count_per_query):
            h = hashlib.md5(f"{query}{j}".encode()).hexdigest()[:6]
            output_path = cat_dir / f"{category}_{h}.jpg"

            if output_path.exists():
                print(f"  Skipping: {output_path.name} (exists)")
                continue

            print(f"\n  [{i+1}/{len(queries)}] Query: {query}")
            if download_unsplash(query, output_path):
                downloaded += 1
            elif download_pexels(query, output_path):
                downloaded += 1

    print(f"\n  Total downloaded for {category}: {downloaded}")
    return downloaded


def download_all(count_per_query: int = 2):
    """Download starter images for all categories."""
    total = 0
    for category, queries in STARTER_QUERIES.items():
        total += download_category(category, queries, count_per_query)
    print(f"\n{'='*40}")
    print(f"  TOTAL: {total} images downloaded")
    print(f"{'='*40}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python download_images.py all")
        print("  python download_images.py business 'office meeting' 5")
        sys.exit(1)

    if sys.argv[1] == "all":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        download_all(count)
    else:
        category = sys.argv[1]
        query = sys.argv[2] if len(sys.argv) > 2 else category
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        download_category(category, [query], count)
