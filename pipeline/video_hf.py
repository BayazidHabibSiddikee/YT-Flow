#!/usr/bin/env python3
"""Marin Pipeline — HuggingFace + Kaggle Video Generation

Uses free HuggingFace Inference API and Kaggle GPU notebooks
for text-to-video generation. No paid API needed.

Models used:
- CogVideoX (HF Inference API — free tier)
- Stable Video Diffusion (HF Spaces — free GPU)
- Kaggle GPU notebooks for heavier models
"""

import time
import requests
from pathlib import Path
from huggingface_hub import InferenceClient

from config import KAGGLE_API_TOKEN


class HFVideoGenerator:
    """Video generation via HuggingFace free inference API."""

    def __init__(self):
        self.client = InferenceClient()  # Uses HF_TOKEN env or anonymous
        self.space_url = "https://hf-m.space"  # Inference proxy

    def text_to_video_cogvideox(
        self,
        prompt: str,
        output_path: Path,
        num_frames: int = 49,
    ) -> Path:
        """Generate video using CogVideoX via HF Inference API (free)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"[HF] Generating video with CogVideoX...")
        print(f"[HF] Prompt: {prompt[:80]}...")

        try:
            # Try the dedicated CogVideoX space
            video_bytes = self.client.text_to_video(
                prompt,
                model="THUDM/CogVideoX-2b",
            )
            output_path.write_bytes(video_bytes)
            print(f"[HF] CogVideoX done: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
            return output_path

        except Exception as e:
            print(f"[HF] CogVideoX failed: {e}")
            raise

    def text_to_video_generic(
        self,
        prompt: str,
        output_path: Path,
    ) -> Path:
        """Generate video using any available free model on HF Spaces."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try free HF Spaces that host video generation
        spaces = [
            "THUDM/CogVideoX-5B-Space",
            "multimodalart/stable-video-diffusion",
            "a]li-vilab/i2vgen-xl",
        ]

        for space in spaces:
            try:
                print(f"[HF] Trying {space}...")
                video_bytes = self.client.text_to_video(prompt, model=space)
                output_path.write_bytes(video_bytes)
                if output_path.stat().st_size > 10000:
                    print(f"[HF] Success with {space}: {output_path.name}")
                    return output_path
            except Exception as e:
                print(f"[HF] {space} failed: {e}")
                continue

        raise RuntimeError("All HF video models failed")


class KaggleVideoGenerator:
    """Video generation via Kaggle GPU notebooks (free T4/P100)."""

    def __init__(self):
        self.api_token = KAGGLE_API_TOKEN
        self.available = bool(self.api_token)

    def generate_video(
        self,
        prompt: str,
        output_path: Path,
        model: str = "modelscope/text-to-video-ms-1.7b",
    ) -> Path:
        """Submit a Kaggle notebook job for video generation."""
        if not self.available:
            raise RuntimeError("Kaggle API token not configured")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create notebook script
        notebook_code = f'''
# Kaggle GPU Video Generation
# Model: {model}

import torch
from diffusers import TextToVideoSDPipeline

print("Loading model: {model}")
pipe = TextToVideoSDPipeline.from_pretrained(
    "{model}",
    torch_dtype=torch.float16,
)
pipe.to("cuda")

print("Generating video...")
prompt = """{prompt.replace('"', '\\"')}"""
result = pipe(prompt, num_frames=32, guidance_scale=7.5)
video = result.frames[0]

# Save as MP4
import imageio
imageio.mimsave("output.mp4", video, fps=8)
print("Video saved: output.mp4")
'''

        # Save notebook with kernel-metadata.json
        nb_dir = output_path.parent / "kaggle_notebook"
        nb_dir.mkdir(parents=True, exist_ok=True)

        nb_path = nb_dir / "main.py"
        nb_path.write_text(notebook_code)

        # Write kernel-metadata.json
        import json
        meta = {
            "id": f"sword/video-gen-{hash(prompt) % 100000}",
            "title": f"Video Gen - {hash(prompt) % 100000}",
            "code_file": "main.py",
            "language": "python",
            "kernel_type": "notebook",
            "enable_gpu": True,
            "enable_internet": True,
        }
        meta_path = nb_dir / "kernel-metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2))

        print(f"[Kaggle] Submitting GPU notebook job...")
        import subprocess
        result = subprocess.run(
            ["kaggle", "kernels", "push", "-p", str(nb_dir), "--accelerator", "GPU"],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode == 0:
            print(f"[Kaggle] Job submitted. Check: https://www.kaggle.com/code")
            print(f"[Kaggle] Output will be at: {output_path}")
        else:
            print(f"[Kaggle] Submit failed: {result.stderr[:300]}")

        return output_path


class VideoGenManager:
    """Unified video generation — tries HF free first, then Kaggle GPU."""

    def __init__(self):
        self.hf = HFVideoGenerator()
        self.kaggle = KaggleVideoGenerator()

    def generate(
        self,
        prompt: str,
        output_path: Path,
        method: str = "auto",
    ) -> Path:
        """
        Generate video from prompt.
        method: "hf" (HuggingFace), "kaggle" (Kaggle GPU), "auto" (try both)
        """
        if method == "hf" or method == "auto":
            try:
                return self.hf.text_to_video_generic(prompt, output_path)
            except Exception as e:
                if method == "hf":
                    raise
                print(f"[VideoGen] HF failed: {e}, trying Kaggle...")

        if method == "kaggle" or method == "auto":
            if self.kaggle.available:
                return self.kaggle.generate_video(prompt, output_path)
            else:
                print("[VideoGen] Kaggle not available")

        raise RuntimeError("No video generation method available")


if __name__ == "__main__":
    gen = VideoGenManager()
    print(f"HF: available")
    print(f"Kaggle: {'available' if gen.kaggle.available else 'no token'}")
