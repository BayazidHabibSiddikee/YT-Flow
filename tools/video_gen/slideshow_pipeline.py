#!/usr/bin/env python3
"""Image slideshow video pipeline - no API keys needed."""
import subprocess
import sys
from pathlib import Path
import argparse
import json
from typing import List, Optional
import re

# Configuration
OUTPUT_DIR = Path.home() / "Documents" / "video_gen" / "downloads"
IMAGES_DIR = Path.home() / "Documents" / "video_gen" / "images"  # Put your images here

def get_images(directory: Path) -> List[Path]:
    """Get all image files from directory."""
    if not directory.exists():
        print(f"[ERROR] Images directory not found: {directory}")
        return []
    
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp", "*.gif"]
    images = []
    for ext in extensions:
        images.extend(directory.glob(ext))
        images.extend(directory.glob(ext.upper()))
    
    return sorted(images)

def generate_text_overlays(images: List[Path], text: str, interval: int = 4) -> List[dict]:
    """Generate text overlay instructions for each image."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    overlays = []
    
    for i, img in enumerate(images):
        # Select text based on position
        text_idx = min(i * interval // 4, len(sentences) - 1) if sentences else 0
        
        # Get a snippet of text
        if sentences:
            snippet = sentences[text_idx % len(sentences)]
            if len(snippet) > 100:
                snippet = snippet[:97] + "..."
        else:
            snippet = f"Image {i + 1} of {len(images)}"
        
        overlays.append({
            "image": str(img),
            "text": snippet,
            "duration": interval
        })
    
    return overlays

def generate_slideshow(
    images: List[Path],
    text_overlays: List[dict],
    output_path: Path,
    fps: int = 24,
    resolution: tuple = (1920, 1080)
) -> Optional[Path]:
    """Generate slideshow video with ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create filter complex for each image
    filter_parts = []
    duration_total = 0
    
    for i, overlay in enumerate(text_overlays):
        img_path = overlay["image"]
        duration = overlay["duration"]
        
        # Generate text filter
        text = overlay["text"].replace("'", "'")
        filter_parts.append(
            f"[{i}:v]scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,"
            f"pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2"
            f"[img{i}]"
        )
        
        # Add text overlay
        text_y = resolution[1] - 150  # Position from bottom
        filter_parts.append(
            f"[img{i}]drawtext=text='{text}':fontcolor=white:fontsize=48:"
            f"x=(w-text_w)/2:y={text_y}:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            f"[text{i}]"
        )
        
        duration_total += duration
    
    # Concatenate all images
    input_filters = " ".join(filter_parts)
    
    # Create concat filter
    concat_inputs = " ".join([f"[text{i}]" for i in range(len(text_overlays))])
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y"]
    
    # Add all image inputs
    for i in range(len(images)):
        cmd.extend(["-loop", "1", "-t", str(text_overlays[i]["duration"]), "-i", str(images[i])])
    
    # Add filter complex
    cmd.extend(["-filter_complex", input_filters])
    
    # Concatenate
    cmd.extend([
        "-filter_complex",
        f"{concat_inputs}concat=n={len(text_overlays)}:v=1:a=0[outv]"
    ])
    
    # Output
    cmd.extend(["-map", "[outv]", "-c:v", "libx264", "-preset", "fast"])
    cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    cmd.extend(["-r", str(fps)])
    cmd.extend([str(output_path)])
    
    print(f"[INFO] Generating slideshow: {len(images)} images, {duration_total}s total")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if output_path.exists() and output_path.stat().st_size > 10000:
        print(f"[OK] Video generated: {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return output_path
    else:
        print(f"[ERROR] Failed to generate video")
        print(f"STDERR: {result.stderr[:500]}")
        return None

def generate_audio_tts(text: str, output_path: Path) -> Optional[Path]:
    """Generate audio from text using espeak."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            "espeak",
            "-w", str(output_path),
            "--voice", "en",
            "--speed", "150",
            text
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if output_path.exists() and output_path.stat().st_size > 1000:
            print(f"[OK] Audio generated: {output_path}")
            return output_path
        else:
            print(f"[ERROR] espeak failed")
            return None
            
    except Exception as e:
        print(f"[ERROR] Audio generation failed: {e}")
        return None

def merge_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> Optional[Path]:
    """Merge video and audio."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not video_path.exists():
        print(f"[ERROR] Video not found: {video_path}")
        return None
    if not audio_path.exists():
        print(f"[ERROR] Audio not found: {audio_path}")
        return None
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if output_path.exists() and output_path.stat().st_size > 10000:
            print(f"[OK] Merged video: {output_path}")
            return output_path
        else:
            print(f"[ERROR] Merge failed")
            return None
            
    except Exception as e:
        print(f"[ERROR] Merge error: {e}")
        return None

def run_slideshow_pipeline(
    images_dir: Path = IMAGES_DIR,
    text: str = "",
    output_dir: Path = OUTPUT_DIR,
    interval: int = 4,
    use_tts: bool = True,
):
    """Run the complete slideshow pipeline."""
    print("\n" + "=" * 60)
    print("IMAGE SLIDESHOW PIPELINE")
    print("=" * 60 + "\n")
    
    # Get images
    images = get_images(images_dir)
    if not images:
        print(f"[ERROR] No images found in {images_dir}")
        print(f"[INFO] Please add images to: {images_dir}")
        return None
    
    print(f"[INFO] Found {len(images)} images")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate text overlays
    if not text:
        text = " ".join([f"Image {i+1}" for i in range(len(images))])
    
    overlays = generate_text_overlays(images, text, interval)
    
    # Generate slideshow video
    video_path = output_dir / "slideshow_video.mp4"
    video = generate_slideshow(images, overlays, video_path)
    
    if not video:
        return None
    
    # Generate audio
    audio_path = output_dir / "audio.wav"
    if use_tts:
        audio = generate_audio_tts(text, audio_path)
    else:
        # Try to use existing audio file
        audio_files = list(output_dir.glob("*.wav")) + list(output_dir.glob("*.mp3"))
        if audio_files:
            audio_path = audio_files[0]
            audio = audio_path
            print(f"[INFO] Using existing audio: {audio}")
        else:
            audio = None
            print("[INFO] No audio generated")
    
    # Merge if both exist
    if video and audio:
        final_path = output_dir / "final_slideshow.mp4"
        result = merge_video_audio(video, audio, final_path)
        if result:
            print(f"\n{'='*60}")
            print(f"[COMPLETE] Final video: {result}")
            print(f"{'='*60}")
            return result
    elif video:
        print(f"\n{'='*60}")
        print(f"[COMPLETE] Video (no audio): {video}")
        print(f"{'='*60}")
        return video
    
    return None

def main():
    parser = argparse.ArgumentParser(description="Image slideshow video pipeline")
    parser.add_argument("--images", default=str(IMAGES_DIR), help="Directory with images")
    parser.add_argument("--text", help="Text to display (or use TTS for audio)")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--interval", type=int, default=4, help="Seconds per image")
    parser.add_argument("--no-tts", action="store_true", help="Skip TTS audio generation")
    
    args = parser.parse_args()
    
    images_dir = Path(args.images)
    output_dir = Path(args.output)
    
    result = run_slideshow_pipeline(
        images_dir=images_dir,
        text=args.text,
        output_dir=output_dir,
        interval=args.interval,
        use_tts=not args.no_tts,
    )
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
