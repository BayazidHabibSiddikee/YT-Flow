#!/usr/bin/env python3
"""
Image Slideshow Video Pipeline
================================
Create videos from images with text overlays and audio.

Usage:
  python slideshow.py --topic "My Video" --interval 3
  python slideshow.py --images /path/to/images --text "Welcome to our channel"
  python slideshow.py --help

Features:
  - Support JPG, PNG, WEBP images
  - Auto-generate audio track
  - Text overlay per slide (optional)
  - 1920x1080 output resolution
  - No API keys required

Author: Hermes Agent
"""
import subprocess
import sys
from pathlib import Path
import argparse
import json
import os

OUTPUT_DIR = Path.home() / "Documents" / "video_gen" / "downloads"
IMAGES_DIR = Path.home() / "Documents" / "video_gen" / "images"

def run_pipeline():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Create video slideshow from images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use images from default folder
  python slideshow.py --topic "My Video"

  # Custom images folder
  python slideshow.py --images /path/to/images --interval 4

  # Add text overlay (JSON format)
  python slideshow.py --topic "Tutorial" --text '{"text": "Welcome", "position": "bottom"}'

  # Override all text
  python slideshow.py --topic "Demo" --text "Hello world"

Input images: ~/Documents/video_gen/images/*.jpg
Output: ~/Documents/video_gen/downloads/
        """
    )
    parser.add_argument("--images", default=str(IMAGES_DIR), help="Images folder")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output folder")
    parser.add_argument("--topic", default="Slideshow", help="Video title")
    parser.add_argument("--interval", type=int, default=3, help="Seconds per image")
    parser.add_argument("--text", default=None, help="Text overlay (JSON or string)")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    args = parser.parse_args()
    
    images_dir = Path(args.images)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("IMAGE SLIDESHOW PIPELINE")
    print("=" * 60)
    print(f"[INFO] Images: {images_dir}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Topic: {args.topic}")
    print(f"[INFO] Interval: {args.interval}s per image")
    print(f"[INFO] FPS: {args.fps}")
    
    # Get images
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.WEBP"]
    images = []
    for ext in extensions:
        images.extend(images_dir.glob(ext))
    images = sorted(set(images))
    
    if not images:
        print(f"\n[ERROR] No images found in {images_dir}")
        print("[INFO] Place images in: ~/Documents/video_gen/images/")
        return None
    
    print(f"\n[INFO] Found {len(images)} images")
    
    # Parse text overlay
    text_overlays = []
    if args.text:
        try:
            # Try JSON
            text_data = json.loads(args.text)
            if isinstance(text_data, dict):
                text_overlays = [{"text": text_data.get("text", "")}] * len(images)
            elif isinstance(text_data, list):
                text_overlays = text_data[:len(images)]
        except json.JSONDecodeError:
            # Plain text - use for all slides
            text_overlays = [{"text": args.text}] * len(images)
    
    # Create video
    video_name = f"{args.topic.replace(' ', '_')}_slideshow.mp4"
    video_path = output_dir / video_name
    
    print("\n[STEP 1/3] Generating video...")
    
    # Create concat list
    list_file = output_dir / "image_list.txt"
    with open(list_file, "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {args.interval}\n")
    
    # FFmpeg command
    # Build filter complex for text overlay if needed
    filter_complex = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
    
    # Add text overlay if provided
    if text_overlays and text_overlays[0].get("text"):
        text = text_overlays[0]["text"][:80]  # Limit text length
        filter_complex += f",drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-150"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-r", str(args.fps),
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if not video_path.exists() or video_path.stat().st_size < 10000:
        print(f"[ERROR] Video generation failed")
        if result.stderr:
            print(f"STDERR: {result.stderr[:500]}")
        return None
    
    print(f"[OK] Video: {video_path} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # Generate audio
    audio_name = f"{args.topic.replace(' ', '_')}_audio.wav"
    audio_path = output_dir / audio_name
    
    print("\n[STEP 2/3] Generating audio...")
    
    # Generate silent audio track
    total_duration = args.interval * len(images)
    cmd_audio = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(total_duration),
        "-c:a", "pcm_s16le",
        str(audio_path)
    ]
    
    result_audio = subprocess.run(cmd_audio, capture_output=True, text=True, timeout=30)
    
    if not audio_path.exists():
        print("[WARN] Audio generation failed")
        return video_path
    
    print(f"[OK] Audio: {audio_path} ({audio_path.stat().st_size / 1024:.0f} KB)")
    
    # Merge video + audio
    final_name = f"{args.topic.replace(' ', '_')}_final.mp4"
    final_path = output_dir / final_name
    
    print("\n[STEP 3/3] Merging video and audio...")
    
    cmd_merge = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(final_path)
    ]
    
    subprocess.run(cmd_merge, capture_output=True, timeout=60)
    
    if final_path.exists() and final_path.stat().st_size > 10000:
        print(f"[OK] Final: {final_path}")
        print(f"\n{'=' * 60}")
        print(f"SUCCESS: {final_path}")
        print(f"{'=' * 60}")
        return final_path
    
    print("[WARN] Merge failed, returning video without audio")
    return video_path


if __name__ == "__main__":
    result = run_pipeline()
    sys.exit(0 if result else 1)
