"""Create a 10-second fitness video matching the Deku reference style."""
import subprocess, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, "pipeline/output/images/deku_fitness")
AUDIO = os.path.join(IMG_DIR, "voiceover.mp3")
OUTPUT = os.path.join(IMG_DIR, "deku_fitness_short.mp4")

# Text overlays per image
TEXTS = [
    ("DISCIPLINE", "IS NOT A PUNISHMENT"),
    ("IT IS A PROMISE", "YOU MAKE TO YOURSELF"),
    ("EVERY REP", "EVERY SET"),
    ("UNSTOPPABLE", ""),
]

# Ken Burns zoom per image (start_zoom, end_zoom)
ZOOMS = [
    (1.0, 1.15),   # pull-ups: slow zoom in
    (1.1, 1.0),    # treadmill: slow zoom out
    (1.0, 1.2),    # dumbbells: zoom in (power)
    (1.05, 1.0),   # success: slight zoom out (reveal)
]

# Duration per image (total ~10.2s)
DUR = 2.55

def create_video():
    # Build FFmpeg filter for each image
    inputs = []
    filter_parts = []

    names = ["01_pullups", "02_treadmill", "03_dumbbells", "04_success"]
    for i in range(4):
        img = os.path.join(IMG_DIR, f"{names[i]}.jpg")
        inputs += ["-loop", "1", "-t", str(DUR), "-i", img]

        z0, z1 = ZOOMS[i]
        t1, t2 = TEXTS[i]

        # Ken Burns zoom
        filter_parts.append(
            f"[{i}:v]scale=720:1280,"
            f"zoompan=z='min({z0}+({z1}-{z0})*on/({DUR}*24),1.5)'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={int(DUR*24)}:s=720x1280:fps=24,"
            f"drawtext=text='{t1}':fontcolor=white:fontsize=52"
            f":x=(w-text_w)/2:y=h/2-80:borderw=3:bordercolor=black,"
            f"drawtext=text='{t2}':fontcolor=white:fontsize=40"
            f":x=(w-text_w)/2:y=h/2+10:borderw=2:bordercolor=black"
            f"[v{i}]"
        )

    # Concat all segments
    concat = "".join(f"[v{i}]" for i in range(4))
    filter_parts.append(f"{concat}concat=n=4:v=1:a=0[outv]")

    filter_complex = ";\n".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", AUDIO,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "4:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "10.2",
        "-movflags", "+faststart",
        OUTPUT
    ]

    print("Creating video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr[-2000:]}")
        return False

    # Get file size
    size = os.path.getsize(OUTPUT) / 1024 / 1024
    print(f"Video created: {OUTPUT} ({size:.1f} MB)")
    return True

if __name__ == "__main__":
    create_video()
