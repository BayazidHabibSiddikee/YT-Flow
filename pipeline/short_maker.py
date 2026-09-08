#!/usr/bin/env python3
"""
Simple Short Generator — Text + Image + Music (No Voice)

Usage:
    python3 short_maker.py war "The warrior conquers himself"
    python3 short_maker.py gym "Discipline is choosing between what you want now and what you want most"
    python3 short_maker.py spiritual "The soul is neither born, and nor does it die"
"""

import subprocess
import sys
import os
import random
from pathlib import Path

# Base paths
BASE = Path(__file__).parent
IMAGES_DIR = BASE / "collection" / "images"
MUSIC_DIR = BASE / "collection" / "music"
OUTPUT_DIR = BASE / "output" / "shorts"

# Font
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"

# Niche configs
NICHES = {
    "war": {
        "images": "izuku_midoriya",
        "music": "war",
        "font": FONT,
        "fontsize": 36,
        "fontcolor": "white@0.9",
        "shadowcolor": "black@0.6",
    },
    "gym": {
        "images": "motivational",
        "music": "motivational",
        "font": FONT,
        "fontsize": 36,
        "fontcolor": "white@0.9",
        "shadowcolor": "black@0.6",
    },
    "spiritual": {
        "images": "spiritual",
        "music": "spiritual",
        "font": FONT_ITALIC,
        "fontsize": 34,
        "fontcolor": "white@0.9",
        "shadowcolor": "black@0.5",
    },
}


def get_random_file(directory: Path, extensions: list[str]) -> Path:
    """Get a random file from directory with given extensions."""
    files = [f for f in directory.iterdir() if f.suffix.lower() in extensions]
    if not files:
        raise FileNotFoundError(f"No files with extensions {extensions} in {directory}")
    return random.choice(files)


def split_text(text: str, max_lines: int = 3) -> list[str]:
    """Split text into lines for subtitle display."""
    # Remove citations like "— Bhagavad Gita" and handle separately
    citation = ""
    if "—" in text:
        parts = text.split("—")
        text = parts[0].strip()
        citation = "— " + parts[1].strip()
    
    words = text.split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) > 25:  # Shorter lines
            lines.append(" ".join(current))
            current = []
            if len(lines) >= max_lines:
                break
    if current:
        lines.append(" ".join(current))
    
    # Add citation as last line if present
    if citation and len(lines) < max_lines:
        lines.append(citation)
    
    return lines[:max_lines]


def escape_ffmpeg(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    return text.replace(":", "\\:").replace("'", "\\'").replace("%", "%%")


def create_short(niche: str, text: str, duration: int = 18, output_name: str = None):
    """Create a short video with text overlay, image, and music."""
    config = NICHES.get(niche)
    if not config:
        print(f"Unknown niche: {niche}. Available: {list(NICHES.keys())}")
        return None

    # Get random image and music
    try:
        image_path = get_random_file(IMAGES_DIR / config["images"], [".jpg", ".jpeg", ".png"])
        music_path = get_random_file(MUSIC_DIR / config["music"], [".mp3", ".wav", ".ogg"])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None

    # Output path
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_name:
        output_path = OUTPUT_DIR / f"{output_name}.mp4"
    else:
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()[:6]
        output_path = OUTPUT_DIR / f"{niche}_{h}.mp4"

    # Split text into lines
    lines = split_text(text)

    # Build drawtext filters - NO OVERLAP, sequential timing
    text_filters = []
    time_per_line = (duration - 4) / len(lines)  # Leave 2s at start and end

    for i, line in enumerate(lines):
        start_time = 2 + i * time_per_line
        end_time = start_time + time_per_line  # No overlap
        
        # Position varies slightly for visual interest
        y_pos = 0.75 if i % 2 == 0 else 0.78

        filter_str = (
            f"drawtext=text='{escape_ffmpeg(line)}':"
            f"fontfile={config['font']}:"
            f"fontsize={config['fontsize']}:"
            f"fontcolor={config['fontcolor']}:"
            f"shadowcolor={config['shadowcolor']}:"
            f"shadowx=2:shadowy=2:"
            f"x=(w-text_w)/2:y=h*{y_pos}:"
            f"enable='between(t,{start_time:.1f},{end_time:.1f})'"
        )
        text_filters.append(filter_str)

    # Build FFmpeg command
    vf_chain = (
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        + ",".join(text_filters)
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", str(music_path),
        "-vf", vf_chain,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-t", str(duration),
        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"[{niche}] Creating: {output_path.name}")
    print(f"  Image: {image_path.name}")
    print(f"  Music: {music_path.name}")
    print(f"  Text: {lines}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if result.returncode == 0:
        size = output_path.stat().st_size
        print(f"  OK: {size // 1024}KB")
        return output_path
    else:
        print(f"  FAILED: {result.stderr[:200]}")
        return None


def batch_generate(count_per_niche: int = 3):
    """Generate multiple shorts for each niche."""
    quotes = {
        "war": [
            "The warrior who conquers himself is greater than one who conquers a thousand men in battle",
            "In the midst of chaos, there is also opportunity",
            "The supreme art of war is to subdue the enemy without fighting",
            "He who knows when he can fight and when he cannot will be victorious",
            "Every battle is won before it is ever fought",
        ],
        "gym": [
            "Discipline is choosing between what you want now and what you want most",
            "The pain you feel today will be the strength you feel tomorrow",
            "Your body can stand almost anything. It's your mind you have to convince",
            "The only bad workout is the one that didn't happen",
            "Success isn't always about greatness. It's about consistency",
        ],
        "spiritual": [
            "The soul is neither born, and nor does it die — Bhagavad Gita",
            "Peace comes from within. Do not seek it without — Buddha",
            "The only way to do great work is to love what you do — Gandhi",
            "In the middle of difficulty lies opportunity — Albert Einstein",
            "What we think, we become — Buddha",
        ],
    }

    print(f"\n{'='*60}")
    print(f"  BATCH GENERATOR — {count_per_niche} shorts per niche")
    print(f"{'='*60}\n")

    results = []
    for niche, quote_list in quotes.items():
        print(f"\n--- {niche.upper()} ---")
        for i in range(min(count_per_niche, len(quote_list))):
            quote = quote_list[i]
            path = create_short(niche, quote, duration=18)
            if path:
                results.append(path)

    print(f"\n{'='*60}")
    print(f"  Generated {len(results)} shorts")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 short_maker.py <niche> <text>")
        print("  python3 short_maker.py batch [count]")
        print(f"\nNiches: {list(NICHES.keys())}")
        sys.exit(1)

    if sys.argv[1] == "batch":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        batch_generate(count)
    else:
        niche = sys.argv[1]
        text = " ".join(sys.argv[2:])
        create_short(niche, text)
