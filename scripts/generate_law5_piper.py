#!/usr/bin/env python3
"""Generate 60-second cinematic video for Law V with Piper TTS audio."""

from pathlib import Path
import os
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Settings
BASE_DIR = Path(__file__).parent
DURATION = 60  # seconds
FPS = 30
WIDTH = 1920
HEIGHT = 1080
OUTPUT_DIR = str(BASE_DIR / "video_gen" / "downloads")
PIPER_VOICES_DIR = BASE_DIR / "Audio_&_voices" / "piper-voices"

# Law V full text for narration
NARRATION = """Law Five: Get others to come to you. Use bait, if necessary.

When you force the enemy to come to you, you take away his strength, his choice, and his momentum.

Every move you make is reactive, forced, out of balance.

Keep your options open. Never get so invested in a strategy that you are forced to use it.

Let the enemy strive to win your favor. Always make your opponents work hard to get to you.

Force them to travel unfamiliar terrain. Put them in a position of weakness.

And when they arrive at your doorstep, you will have already laid your trap.

They will be weak, tired, and exposed. You will be strong, well rested, and ready."""

def generate_audio():
    """Generate Piper TTS audio."""
    audio_path = os.path.join(OUTPUT_DIR, "law5_piper_full.wav")
    cmd = [
        "piper",
        "-m", str(PIPER_VOICES_DIR / "en_US-ryan-medium.onnx"),
        "-c", str(PIPER_VOICES_DIR / "en_US-ryan-medium.onnx.json"),
        "-f", audio_path
    ]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        stdout, stderr = proc.communicate(input=NARRATION.encode())
    
    if proc.returncode != 0:
        print(f"Audio generation failed: {stderr.decode()}")
        return None
    
    return audio_path

def get_background(t, frame_idx):
    """Create dark cinematic gradient background."""
    phase = t * 0.3
    r1 = int(8 + 5 * math.sin(phase))
    g1 = int(6 + 4 * math.sin(phase + 2))
    b1 = int(12 + 6 * math.sin(phase + 4))
    
    r2 = int(18 + 8 * math.sin(phase * 0.7))
    g2 = int(14 + 6 * math.sin(phase * 0.7 + 1))
    b2 = int(28 + 10 * math.sin(phase * 0.7 + 3))
    
    gradient = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(gradient)
    
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    vignette = Image.new('RGBA', (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    for i in range(800, 0, -5):
        alpha = int(80 * (1 - i / 800))
        vdraw.ellipse([WIDTH//2 - i, HEIGHT//2 - i, WIDTH//2 + i, HEIGHT//2 + i],
                     fill=(0, 0, 0, alpha))
    gradient = Image.alpha_composite(gradient.convert('RGBA'), vignette).convert('RGB')
    
    return gradient

def generate_frame(frame_idx, audio_duration, total_frames):
    """Generate a single frame."""
    t = frame_idx / FPS
    
    bg = get_background(t, frame_idx)
    draw = ImageDraw.Draw(bg)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 52)
        author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    gold = (212, 175, 55)
    cream = (255, 248, 220)
    
    progress = t / audio_duration
    
    if progress < 0.15:
        # Phase 1: Title animation (first 15% of video)
        title_progress = progress / 0.15
        scale = min(1, title_progress * 2) if title_progress < 0.5 else 1
        
        title = "LAW V"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = center_x - tw // 2
        y = center_y - th // 2 - 50
        alpha = min(255, int(255 * min(1, title_progress * 2)))
        draw.text((x, y), title, font=title_font, fill=gold)
        
        if title_progress > 0.5:
            subtitle = "Get others to come to you — Use bait, if necessary."
            sbbox = draw.textbbox((0, 0), subtitle, font=text_font)
            sw, sh = sbbox[2] - sbbox[0], sbbox[3] - sbbox[1]
            draw.text((center_x - sw // 2, y + th + 40), subtitle, font=text_font, fill=cream)
    
    elif progress < 0.25:
        # Phase 2: Fade to black
        fade_progress = (progress - 0.15) / 0.1
        # Darken background
        bg_array = np.array(bg)
        fade_mask = int(50 * fade_progress)
        bg_array = np.maximum(0, bg_array - fade_mask).astype(np.uint8)
        Image.fromarray(bg_array).save(f"/tmp/frame_{frame_idx:04d}.png")
        return
    
    else:
        # Phase 3: Full text display
        lines = NARRATION.split('\n')
        line_height = 58
        total_text_height = len([l for l in lines if l.strip()]) * line_height
        start_y = center_y - total_text_height // 2
        
        for i, line in enumerate(lines):
            if line.strip() == '':
                continue
            lbbox = draw.textbbox((0, 0), line, font=text_font)
            lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
            draw.text((center_x - lw // 2, start_y + i * line_height),
                     line, font=text_font, fill=cream)
        
        author_text = "Robert Greene, The 48 Laws of Power"
        abbox = draw.textbbox((0, 0), author_text, font=author_font)
        draw.text((center_x - abbox[2]//2, center_y + total_text_height // 2 + 30),
                 author_text, font=author_font, fill=gold)
    
    # Subtle grain every 5 frames
    if frame_idx % 5 == 0:
        noise = np.random.randint(0, 6, (HEIGHT, WIDTH, 3), dtype=np.uint8)
        noise_img = Image.fromarray(noise)
        bg = Image.blend(bg, noise_img, 0.03)
    
    bg.save(f"/tmp/frame_{frame_idx:04d}.png")

def main():
    print("Generating Piper audio...")
    audio_path = generate_audio()
    if not audio_path:
        print("Failed to generate audio")
        return
    
    # Get actual duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    audio_duration = float(result.stdout.strip())
    print(f"Audio duration: {audio_duration:.1f}s")
    
    # Adjust video to match audio
    total_frames = int(audio_duration * FPS)
    
    print(f"Generating {total_frames} frames...")
    for i in range(total_frames):
        if i % 60 == 0:
            print(f"  Frame {i}/{total_frames} ({100*i//total_frames}%)")
        generate_frame(i, audio_duration, total_frames)
    
    print("Encoding video...")
    video_path = os.path.join(OUTPUT_DIR, "law5_piper_video.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", "/tmp/frame_%04d.png",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        video_path
    ], check=True, capture_output=True)
    
    print("Merging audio...")
    final_path = os.path.join(OUTPUT_DIR, "law5_piper_final.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_path
    ], check=True, capture_output=True)
    
    # Cleanup
    subprocess.run(["rm", "-rf", "/tmp/frame_*.png"])
    
    print(f"Done! Video: {final_path}")
    print(f"Size: {os.path.getsize(final_path) // 1024} KB")

if __name__ == "__main__":
    main()
