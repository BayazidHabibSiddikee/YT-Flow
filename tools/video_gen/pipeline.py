#!/usr/bin/env python3
"""
Complete Video Pipeline: Generate → Audio → Merge → Post to Social Media
===========================================================================
Usage:
  python pipeline.py --topic "The Future of AI" --output /path/to/output.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

PIPELINE_DIR = Path(__file__).parent
OUTPUT_DIR = PIPELINE_DIR.parent / "downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load API keys from .env
def load_env():
    env_file = PIPELINE_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

# API Keys
API_KEYS = {
    "fal": os.environ.get("FAL_KEY", ""),
    "youtube": os.environ.get("YOUTUBE_API_KEY", ""),
    "facebook": os.environ.get("FACEBOOK_PAGE_TOKEN", ""),
    "instagram": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
    "tiktok": os.environ.get("TIKTOK_ACCESS_TOKEN", ""),
    "kaggle": {
        "username": os.environ.get("KAGGLE_USERNAME", ""),
        "key": os.environ.get("KAGGLE_KEY", ""),
    }
}

print(f"[INFO] FAL_KEY loaded: {'YES' if API_KEYS['fal'] else 'NO'}")

# ============================================================================
# VIDEO GENERATION
# ============================================================================

def generate_video_falai(topic: str, duration: int = 30) -> Optional[Path]:
    """Generate video using fal.ai API (text-to-video)."""
    if not API_KEYS["fal"]:
        print("[WARN] FAL_KEY not set. Skipping fal.ai video generation.")
        return None
    
    try:
        import fal_client
    except ImportError:
        print("[ERROR] fal-client not installed. Run: pip install fal-client")
        return None
    
    try:
        print(f"[INFO] Generating video via fal.ai: {topic}")
        print("[INFO] This may take 1-3 minutes...")
        
        # Use fal_client.run directly with model name
        result = fal_client.run(
            "fal-ai/wan-t2v",
            arguments={
                "prompt": topic,
                "num_frames": 25,
                "height": 480,
                "width": 854,
            },
            timeout=300,
        )
        
        output_path = OUTPUT_DIR / f"{topic.replace(' ', '_')}_fal.mp4"
        
        # Download the generated video
        import requests
        if hasattr(result, 'image') and result.image:
            response = requests.get(result.image)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] fal.ai Video saved: {output_path}")
            return output_path
        
        # Handle video URL if available
        if hasattr(result, 'video') and result.video:
            response = requests.get(result.video)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] fal.ai Video saved: {output_path}")
            return output_path
            
        print(f"[WARN] fal.ai prediction response: {result}")
        return None
        
    except Exception as e:
        print(f"[ERROR] fal.ai generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_video_slideshow(topic: str, duration: int = 60) -> Optional[Path]:
    """Generate a simple slideshow video (fallback)."""
    output_path = OUTPUT_DIR / f"{topic.replace(' ', '_')}_slideshow.mp4"

    print(f"[INFO] Generating slideshow video: {topic}")

    # Use ffmpeg to create a static video with text overlay
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=blue:s=1920x1080:d={duration}",
            "-vf", f"drawtext=text='{topic}':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if output_path.exists() and output_path.stat().st_size > 10000:
            print(f"[OK] Slideshow video: {output_path} ({output_path.stat().st_size / 1024:.0f}KB)")
            return output_path
        else:
            print(f"[ERROR] Slideshow generation failed: {result.stderr[:300]}")
            return None

    except Exception as e:
        print(f"[ERROR] Frame concatenation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
# ============================================================================

def generate_audio_piper(text: str, output_path: Path) -> Optional[Path]:
    """Generate audio using Piper TTS (local, no GPU needed)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Find Piper model
    piper_models = PIPELINE_DIR.parent.parent / "Audio_&_voices" / "piper-voices"
    if piper_models.exists():
        model_file = list(piper_models.glob("*.onnx"))[0] if list(piper_models.glob("*.onnx")) else None
        if model_file:
            try:
                cmd = [
                    "piper",
                    "-m", str(model_file),
                    "-c", str(model_file).replace(".onnx", ".json"),
                    "-f", str(output_path)
                ]
                with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                    stdout, stderr = proc.communicate(input=text.encode(), timeout=60)
                
                if proc.returncode == 0 and output_path.exists():
                    print(f"[OK] Piper audio: {output_path}")
                    return output_path
                else:
                    print(f"[WARN] Piper failed: {stderr.decode()[:200]}")
            except Exception as e:
                print(f"[ERROR] Piper TTS failed: {e}")
    
    return None


def generate_audio_espeak(text: str, output_path: Path) -> Optional[Path]:
    """Fallback audio generation using espeak."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = ["espeak", "-w", str(output_path), text]
    result = subprocess.run(cmd, capture_output=True)
    
    if output_path.exists() and output_path.stat().st_size > 1000:
        print(f"[OK] espeak audio: {output_path}")
        return output_path
    return None


# ============================================================================
# MERGE VIDEO + AUDIO
# ============================================================================

def merge_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> Optional[Path]:
    """Merge video and audio using ffmpeg."""
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
            print(f"[OK] Merged video: {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
            return output_path
        else:
            print(f"[ERROR] Merge failed: {result.stderr[:300]}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Merge error: {e}")
        return None


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline(
    topic: str,
    duration: int = 60,
    use_fal: bool = True,
    use_vibevoice: bool = False,
):
    """Run the complete video pipeline."""
    print(f"\n{'='*60}")
    print(f"VIDEO PIPELINE: {topic}")
    print(f"{'='*60}\n")
    
    # Step 1: Generate video
    print("[STEP 1/3] Generating video...")
    video_path = None
    
    if use_fal and API_KEYS["fal"]:
        video_path = generate_video_falai(topic, duration)
    
    if not video_path:
        print("[INFO] Using fallback slideshow generation...")
        video_path = generate_video_slideshow(topic, duration)
    
    if not video_path:
        print("[ERROR] Failed to generate video.")
        return None
    
    # Step 2: Generate audio
    print(f"\n[STEP 2/3] Generating audio...")
    script = f"Welcome to today's episode about {topic}. "
    script += f"In this video, we'll explore the key aspects of {topic.lower()}. "
    script += f"Let's dive in."
    
    audio_path = OUTPUT_DIR / f"{topic.replace(' ', '_')}_audio.wav"
    
    # Try Piper first, then espeak
    if not use_vibevoice:
        audio_path = generate_audio_piper(script, audio_path)
        if not audio_path:
            print("[INFO] Piper not available, trying espeak...")
            espeak_path = audio_path.with_suffix('.wav') if audio_path else OUTPUT_DIR / f"{topic.replace(' ', '_')}_audio.wav"
            audio_path = generate_audio_espeak(script, espeak_path)
    else:
        print("[INFO] VibeVoice not yet implemented. Using espeak fallback.")
        audio_path = generate_audio_espeak(script, audio_path)
    
    if not audio_path:
        print("[ERROR] Failed to generate audio.")
        return None
    
    # Step 3: Merge video + audio
    print(f"\n[STEP 3/3] Merging video and audio...")
    final_path = OUTPUT_DIR / f"{topic.replace(' ', '_')}_final.mp4"
    final_path = merge_video_audio(video_path, audio_path, final_path)
    
    if not final_path:
        print("[ERROR] Failed to merge video and audio.")
        return None
    
    print(f"\n{'='*60}")
    print(f"[COMPLETE] Final video: {final_path}")
    print(f"{'='*60}\n")
    return final_path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Generation Pipeline")
    parser.add_argument("--topic", required=True, help="Video topic/title")
    parser.add_argument("--duration", type=int, default=30, help="Video duration in seconds")
    parser.add_argument("--no-fal", action="store_true", help="Skip fal.ai video generation")
    parser.add_argument("--vibevoice", action="store_true", help="Use VibeVoice for audio (requires GPU)")
    parser.add_argument("--output", help="Output path for final video")
    
    args = parser.parse_args()
    
    result = run_pipeline(
        topic=args.topic,
        duration=args.duration,
        use_fal=not args.no_fal,
        use_vibevoice=args.vibevoice,
    )
