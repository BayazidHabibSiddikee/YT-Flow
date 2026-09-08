#!/usr/bin/env python3
"""
Kaggle GPU Video Generation for Izuku Midoriya
Uses CogVideoX or similar model on Kaggle's free T4 GPU
"""

import subprocess
import json
import os
import time
from pathlib import Path

KAGGLE_DIR = Path.home() / "Documents" / "socio_business" / "pipeline" / "kaggle_video"
KAGGLE_DIR.mkdir(parents=True, exist_ok=True)


def create_video_notebook(prompt: str, output_name: str) -> Path:
    """Create a Kaggle notebook for video generation."""
    
    notebook_code = f'''
# Kaggle GPU Video Generation — Izuku Midoriya
# Model: CogVideoX-2B (free T4 GPU)

import torch
from diffusers import CogVideoXPipeline

print("Loading CogVideoX-2B...")
pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-2B",
    torch_dtype=torch.float16,
)
pipe.to("cuda")

print("Generating video...")
prompt = """{prompt}"""
video = pipe(
    prompt=prompt,
    num_frames=49,
    guidance_scale=6.0,
    num_inference_steps=50,
).frames[0]

# Save video
import imageio
output_path = "{output_name}.mp4"
imageio.mimsave(output_path, video, fps=8)
print(f"Video saved: {{output_path}}")
print(f"Duration: {{len(video)/8:.1f}}s")
'''
    
    # Create notebook directory
    nb_dir = KAGGLE_DIR / f"video_{output_name}"
    nb_dir.mkdir(parents=True, exist_ok=True)
    
    # Write main.py
    nb_path = nb_dir / "main.py"
    nb_path.write_text(notebook_code)
    
    # Write kernel-metadata.json - ID must be username/kernel-slug
    slug = f"video-gen-{output_name}".replace("_", "-").replace(" ", "-")
    meta = {
        "id": f"sword/{slug}",
        "title": f"Video Gen {output_name}",
        "code_file": "main.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "machine_shape": "",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": []
    }
    meta_path = nb_dir / "kernel-metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    
    return nb_dir


def submit_to_kaggle(nb_dir: Path) -> bool:
    """Submit notebook to Kaggle GPU."""
    try:
        result = subprocess.run(
            ["kaggle", "kernels", "push", "-p", str(nb_dir), "--accelerator", "GPU"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"  Submitted: {nb_dir.name}")
            print(f"  Check: https://www.kaggle.com/code")
            return True
        else:
            print(f"  Failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def generate_izuku_video(quote: str) -> Path:
    """Generate AI video for Izuku Midoriya quote."""
    import hashlib
    h = hashlib.md5(quote.encode()).hexdigest()[:6]
    
    # Build cinematic prompt
    prompt = (
        f"Cinematic anime style, old war veteran sitting by campfire, "
        f"ruined city in background, dramatic orange firelight, "
        f"dark moody atmosphere, emotional, detailed, 4k quality. "
        f"Scene: {quote}"
    )
    
    print(f"[Kaggle] Generating video for: {quote[:50]}...")
    nb_dir = create_video_notebook(prompt, f"izuku_{h}")
    
    if submit_to_kaggle(nb_dir):
        print(f"[Kaggle] Notebook submitted. Check Kaggle for output.")
        return nb_dir / f"izuku_{h}.mp4"
    else:
        print(f"[Kaggle] Submission failed.")
        return None


# Example usage
if __name__ == "__main__":
    quotes = [
        "The warrior who conquers himself is greater than one who conquers a thousand men in battle",
        "In the midst of chaos, there is also opportunity",
        "Every battle is won before it is ever fought",
    ]
    
    for quote in quotes:
        generate_izuku_video(quote)
        time.sleep(2)
