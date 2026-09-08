#!/usr/bin/env python3
"""Generate a cinematic video for Law V of 48 Laws of Power."""

from pathlib import Path
import tempfile

# Config
BASE_DIR = Path(__file__).parent
WIDTH = 1920
HEIGHT = 1080
FPS = 30
OUTPUT_PATH = str(BASE_DIR / "video_gen" / "downloads" / "law5_video.mp4")
AUDIO_PATH = str(BASE_DIR / "video_gen" / "downloads" / "law5_audio.ogg")

# Colors
BG_DARK = (15, 12, 20)
BG_MID = (25, 20, 35)
GOLD = (212, 175, 55)
GOLD_LIGHT = (255, 215, 0)
WHITE = (255, 255, 255)
GRAY = (180, 175, 190)

def create_gradient_frame(t, width=WIDTH, height=HEIGHT):
    """Create a dark gradient background with subtle motion."""
    img = Image.new('RGB', (width, height), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # Subtle radial gradient effect
    cx, cy = width // 2, height // 2
    for r in range(int(max(width, height) * 0.7), 0, -50):
        alpha = int(30 * (1 - r / (max(width, height) * 0.7)))
        color = (BG_MID[0] + alpha, BG_MID[1] + alpha // 2, BG_MID[2] + alpha // 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    
    # Subtle animated particles (stars)
    np.random.seed(42)
    for _ in range(50):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        brightness = np.random.randint(40, 80)
        draw.ellipse([x, y, x+2, y+2], fill=(brightness, brightness, brightness + 10))
    
    return np.array(img)

def get_font(size):
    """Get font, fallback to default."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def render_title_frame(frame_num, total_frames):
    """Render the main title frame."""
    img = Image.fromarray(create_gradient_frame(frame_num))
    draw = ImageDraw.Draw(img)
    
    # Fade in effect
    progress = min(1.0, frame_num / 60)  # 2 seconds fade in
    
    # Law number
    title_text = "LAW V"
    font_large = get_font(120)
    bbox = draw.textbbox((0, 0), title_text, font=font_large)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    y = 300
    
    # Gold gradient text effect
    draw.text((x, y), title_text, font=font_large, fill=GOLD_LIGHT)
    
    # Subtitle
    subtitle = "Get others to come to you"
    font_mid = get_font(56)
    bbox = draw.textbbox((0, 0), subtitle, font=font_mid)
    text_width = bbox[2] - bbox[0]
    draw.text((x, y + 140), subtitle, font=font_mid, fill=WHITE)
    
    # Quote
    quote = "Use bait if necessary."
    font_small = get_font(36)
    bbox = draw.textbbox((0, 0), quote, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text((x, y + 210), quote, font=font_small, fill=GRAY)
    
    # Source
    source = "— Robert Greene, The 48 Laws of Power"
    font_tiny = get_font(28)
    bbox = draw.textbbox((0, 0), source, font=font_tiny)
    text_width = bbox[2] - bbox[0]
    draw.text((x, HEIGHT - 120), source, font=font_tiny, fill=(100, 100, 120))
    
    # Decorative line
    line_y = y + 100
    line_width = 400
    draw.line([(WIDTH // 2 - line_width // 2, line_y), 
               (WIDTH // 2 + line_width // 2, line_y)], 
              fill=GOLD, width=2)
    
    return np.array(img)

def render_full_law_frame(frame_num, total_frames):
    """Render the full law text."""
    img = Image.fromarray(create_gradient_frame(frame_num))
    draw = ImageDraw.Draw(img)
    
    # Title
    font_large = get_font(80)
    draw.text((100, 80), "LAW V", font=font_large, fill=GOLD_LIGHT)
    
    # Main text
    law_text = """Get Others to Come to You

Use bait, if necessary, to entice your enemy into
coming to you — and, when he does, you will
discover that he is really your subordinate.

He will be out of balance, worn out by his
journey, and exposed. You, however, will be
strong, well rested, and ready.
"""
    font_body = get_font(42)
    y_pos = 220
    for line in law_text.strip().split('\n'):
        draw.text((100, y_pos), line, font=font_body, fill=WHITE)
        y_pos += 55
    
    # Source
    font_tiny = get_font(28)
    draw.text((100, HEIGHT - 100), "— Robert Greene, The 48 Laws of Power", 
              font=font_tiny, fill=(100, 100, 120))
    
    return np.array(img)

def create_video():
    """Create the video using PIL frames and ffmpeg."""
    print("Generating video frames...")
    
    total_frames = 180  # 6 seconds at 30fps
    frames = []
    
    # Phase 1: Title (0-60 frames)
    for i in range(60):
        frames.append(render_title_frame(i, total_frames))
    
    # Phase 2: Full law text (60-150 frames)
    for i in range(90):
        frames.append(render_full_law_frame(i, total_frames))
    
    # Phase 3: Hold (150-180 frames)
    for i in range(30):
        frames.append(render_full_law_frame(90, total_frames))
    
    print(f"Generated {len(frames)} frames")
    
    # Save frames to temp directory
    temp_dir = tempfile.mkdtemp()
    frame_paths = []
    
    for i, frame in enumerate(frames):
        img = Image.fromarray(frame)
        frame_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
        img.save(frame_path)
        frame_paths.append(frame_path)
    
    # Use ffmpeg to create video with audio
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', os.path.join(temp_dir, 'frame_%04d.png'),
        '-i', AUDIO_PATH,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-shortest',
        '-pix_fmt', 'yuv420p',
        OUTPUT_PATH
    ]
    
    print("Encoding video with ffmpeg...")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}")
    
    # Cleanup
    for f in frame_paths:
        os.remove(f)
    os.rmdir(temp_dir)
    
    print(f"Video saved to: {OUTPUT_PATH}")
    return OUTPUT_PATH

if __name__ == "__main__":
    create_video()
