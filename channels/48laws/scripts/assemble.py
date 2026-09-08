#!/usr/bin/env python3
"""Simple video assembler for 48 Laws of Power lessons."""

import subprocess
from pathlib import Path

PIPELINE_DIR = Path.home() / "Documents" / "48laws-pipeline"
IMAGES_DIR = PIPELINE_DIR / "images"
VOICES_DIR = PIPELINE_DIR / "voices"
OUTPUT_DIR = PIPELINE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def assemble_lesson(lesson_num: int) -> Path:
    """Assemble a video from images and audio."""
    img_dir = IMAGES_DIR / f"lesson_{lesson_num:02d}"
    voice_file = VOICES_DIR / f"lesson_{lesson_num:02d}.wav"
    output_file = OUTPUT_DIR / f"law_{lesson_num:02d}.mp4"

    if not img_dir.exists():
        print(f"  No images for lesson {lesson_num}")
        return None

    scenes = sorted(img_dir.glob("scene_*.jpg")) + sorted(img_dir.glob("scene_*.png"))
    if not scenes:
        print(f"  No scene images for lesson {lesson_num}")
        return None

    print(f"  Assembling {len(scenes)} scenes...")

    # Create input file list
    input_list = OUTPUT_DIR / f"input_{lesson_num}.txt"
    with open(input_list, "w") as f:
        for scene in scenes:
            f.write(f"file '{scene}'\n")
            f.write("duration 5\n")
            f.write("repeat 1\n")

    # Simple ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(input_list),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-t", str(len(scenes) * 5),
        str(output_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if output_file.exists() and output_file.stat().st_size > 50000:
        print(f"  ✓ Video: {output_file.name} ({output_file.stat().st_size // 1024}KB)")
        return output_file
    else:
        print(f"  ✗ Failed: {result.stderr[:200]}")
        return None


def assemble_with_audio(lesson_num: int) -> Path:
    """Assemble video with voiceover."""
    img_dir = IMAGES_DIR / f"lesson_{lesson_num:02d}"
    voice_file = VOICES_DIR / f"lesson_{lesson_num:02d}.wav"
    output_file = OUTPUT_DIR / f"law_{lesson_num:02d}.mp4"

    if not img_dir.exists():
        print(f"  No images for lesson {lesson_num}")
        return None

    scenes = sorted(img_dir.glob("scene_*.jpg")) + sorted(img_dir.glob("scene_*.png"))
    if not scenes:
        print(f"  No scene images for lesson {lesson_num}")
        return None

    print(f"  Assembling with audio: {len(scenes)} scenes...")

    # Create input file list
    input_list = OUTPUT_DIR / f"input_{lesson_num}.txt"
    with open(input_list, "w") as f:
        for scene in scenes:
            f.write(f"file '{scene}'\n")
            f.write("duration 5\n")

    # Get audio duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(voice_file)] if voice_file.exists()
        else ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(scenes[0])],
        capture_output=True, text=True
    )

    total_duration = float(probe.stdout.strip() or "15")

    # Assemble video with audio
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(input_list),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30",
    ]

    if voice_file.exists():
        cmd.extend(["-i", str(voice_file), "-c:a", "aac", "-b:a", "128k", "-shortest"])
    else:
        cmd.extend(["-t", str(total_duration)])

    cmd.append(str(output_file))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if output_file.exists() and output_file.stat().st_size > 50000:
        print(f"  ✓ Video: {output_file.name} ({output_file.stat().st_size // 1024}KB)")
        return output_file
    else:
        print(f"  ✗ Failed: {result.stderr[:300]}")
        return None


if __name__ == "__main__":
    import sys
    lesson_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    assemble_with_audio(lesson_num)
