#!/usr/bin/env python3
"""Batch generate YouTube Shorts videos across content pillars."""
import subprocess
import os
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

BASE = Path(__file__).parent.parent
OUTPUT_DIR = BASE / "pipeline" / "output"

# 3 video topics with text overlays and voiceover scripts
VIDEOS = [
    {
        "name": "business_grind",
        "category": "business",
        "images": [
            "man working late office laptop city lights",
            "business handshake deal professional suit",
            "entrepreneur standing tall success view",
            "man writing strategy plan notebook",
        ],
        "texts": [
            ("HUSTLE", "IN SILENCE"),
            ("LET YOUR", "RESULTS SPEAK"),
            ("BUILD IN", "THE DARK"),
            ("SUCCESS", "IS LOUD"),
        ],
        "voiceover": "Hustle in silence. Let your results make the noise. Build in the dark, so success can speak for itself.",
        "title": "Hustle In Silence #Shorts",
        "description": "Hustle in silence. Let your results make the noise.\n\n#Shorts #Motivation #Business #Entrepreneur #Hustle #Success #Mindset",
        "tags": "motivation,business,entrepreneur,hustle,success,shorts",
    },
    {
        "name": "spiritual_peace",
        "category": "spiritual",
        "images": [
            "man praying peaceful golden light spiritual",
            "meditation zen calm morning sunrise",
            "open book bible pages faith",
            "man peaceful nature mountain sunrise",
        ],
        "texts": [
            ("PEACE", "IS A CHOICE"),
            ("STILLNESS", "IS STRENGTH"),
            ("FAITH OVER", "FEAR"),
            ("TRUST THE", "PROCESS"),
        ],
        "voiceover": "Peace is not found. It is chosen. Stillness is strength. Choose faith over fear. Trust the process of your becoming.",
        "title": "Peace Is A Choice #Shorts",
        "description": "Peace is not found. It is chosen. Stillness is strength.\n\n#Shorts #Spiritual #Peace #Faith #Meditation #Mindset",
        "tags": "spiritual,peace,faith,meditation,mindset,shorts",
    },
    {
        "name": "fitness_pain",
        "category": "fitness",
        "images": [
            "muscular man gym training intense dark",
            "man running hard rain determination",
            "boxing training heavy bag fight",
            "man flexing muscle victory gym",
        ],
        "texts": [
            ("PAIN", "IS TEMPORARY"),
            ("QUITTERS", "NEVER WIN"),
            ("EMBRACE", "THE STRUGGLE"),
            ("CHAMPIONS", "ARE MADE"),
        ],
        "voiceover": "Pain is temporary. Quitting lasts forever. Embrace the struggle. Champions are not born. They are made in the gym.",
        "title": "Pain Is Temporary #Shorts",
        "description": "Pain is temporary. Quitting lasts forever.\n\n#Shorts #Fitness #Motivation #Gym #Workout #Discipline",
        "tags": "fitness,motivation,gym,workout,discipline,shorts",
    },
]


def generate_image(query: str, output_path: Path, seed: int) -> bool:
    """Generate image via Pollinations."""
    encoded = urllib.parse.quote(query)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&seed={seed}&nologo=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
            if len(data) > 5000:
                output_path.write_bytes(data)
                print(f"    Image OK: {output_path.name} ({len(data)//1024}KB)")
                return True
    except Exception as e:
        print(f"    Image FAIL: {e}")
    return False


def generate_tts(text: str, output_path: Path) -> bool:
    """Generate voiceover via edge-tts."""
    try:
        import edge_tts
        import asyncio

        async def gen():
            comm = edge_tts.Communicate(text, "en-US-GuyNeural", rate="+5%")
            await comm.save(str(output_path))

        asyncio.run(gen())
        print(f"    TTS OK: {output_path.name}")
        return True
    except Exception as e:
        print(f"    TTS FAIL: {e}")
    return False


def get_duration(path: Path) -> float:
    """Get media duration in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def create_video(video_data: dict) -> Path:
    """Create a single video."""
    name = video_data["name"]
    out_dir = OUTPUT_DIR / "batch" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  Generating: {name}")
    print(f"{'='*50}")

    # Generate 4 images
    print("  [1/3] Generating images...")
    img_paths = []
    for i, query in enumerate(video_data["images"]):
        img_path = out_dir / f"img_{i+1}.jpg"
        if img_path.exists() and img_path.stat().st_size > 5000:
            print(f"    Skip: {img_path.name}")
        else:
            generate_image(query, img_path, seed=hash(name) + i * 111)
        img_paths.append(img_path)

    # Generate TTS
    print("  [2/3] Generating voiceover...")
    tts_path = out_dir / "voiceover.mp3"
    if tts_path.exists() and tts_path.stat().st_size > 1000:
        print(f"    Skip: {tts_path.name}")
    else:
        generate_tts(video_data["voiceover"], tts_path)

    # Create video with FFmpeg
    print("  [3/3] Creating video...")
    duration = get_duration(tts_path)
    dur_per_img = duration / 4

    texts = video_data["texts"]
    filter_parts = []
    for i in range(4):
        t1, t2 = texts[i]
        filter_parts.append(
            f"[{i}:v]scale=720:1280,"
            f"zoompan=z='min(1+0.05*on/{int(dur_per_img*24)},1.5)'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={int(dur_per_img*24)}:s=720x1280:fps=24,"
            f"drawtext=text='{t1}':fontcolor=white:fontsize=56"
            f":x=(w-text_w)/2:y=h/2-80:borderw=3:bordercolor=black,"
            f"drawtext=text='{t2}':fontcolor=white:fontsize=40"
            f":x=(w-text_w)/2:y=h/2+10:borderw=2:bordercolor=black"
            f"[v{i}]"
        )

    concat = "".join(f"[v{i}]" for i in range(4))
    filter_parts.append(f"{concat}concat=n=4:v=1:a=0[outv]")
    filter_complex = ";\n".join(filter_parts)

    # Build input args
    input_args = []
    for p in img_paths:
        input_args += ["-loop", "1", "-t", str(dur_per_img), "-i", str(p)]
    input_args += ["-i", str(tts_path)]

    output_path = out_dir / f"{name}_final.mp4"
    cmd = [
        "ffmpeg", "-y",
        *input_args,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", str(4) + ":a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    FFmpeg FAIL: {result.stderr[-500:]}")
        return None

    size = output_path.stat().st_size / 1024 / 1024
    print(f"    Video OK: {output_path.name} ({size:.1f}MB, {duration:.1f}s)")
    return output_path


def main():
    print("Batch Video Generator")
    print("=" * 50)

    results = []
    for video_data in VIDEOS:
        path = create_video(video_data)
        if path:
            results.append((video_data, path))

    print("\n" + "=" * 50)
    print(f"  Generated {len(results)}/{len(VIDEOS)} videos")
    print("=" * 50)

    # Save metadata for all videos
    metadata_dir = OUTPUT_DIR / "batch"
    for video_data, path in results:
        meta = {
            "title": video_data["title"],
            "description": video_data["description"],
            "tags": video_data["tags"],
            "privacyStatus": "public",
            "video_path": str(path),
        }
        meta_path = metadata_dir / video_data["name"] / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2))
        print(f"  Metadata: {meta_path}")

    return results


if __name__ == "__main__":
    import json
    main()
