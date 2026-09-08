#!/usr/bin/env python3
"""
Direct Kaggle GPU Video Generation using API
"""

import requests
import json
import base64
import time
from pathlib import Path

TOKEN = "KGAT_032972b3c2bee4b6ec2390f7e6462686"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
API_BASE = "https://www.kaggle.com/api/v1"


def create_kernel(title: str, code: str, gpu: bool = True) -> dict:
    """Create a new kernel on Kaggle."""
    url = f"{API_BASE}/kernels/push"
    
    payload = {
        "kernelId": {
            "kernelOwner": "sword",
            "kernelSlug": title.lower().replace(" ", "-").replace("_", "-")[:60]
        },
        "kernelType": "notebook",
        "language": "python",
        "isPrivate": False,
        "enableGpu": gpu,
        "enableInternet": True,
        "kernelDataSources": [],
        "competitionDataSources": [],
        "datasetDataSources": [],
        "meta": {},
        "categoryIds": [],
        "slug": "",
        "title": title,
        "dockerImagePins": [],
        "executionMetadata": {
            "kaggleAccountId": 0,
            "kaggleKernelId": 0,
            "stepNumber": 0
        },
        "outputCode": "",
        "subtitle": "",
        "pinnedVersionId": 0,
        "sessionPinId": 0,
        "source": code,
        "status": "string",
        "validationErrors": [],
        "versionNumber": 0
    }
    
    r = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    return r.json()


def submit_video_generation(prompt: str, output_name: str) -> dict:
    """Submit a video generation kernel."""
    
    code = f'''
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

import imageio
output_path = "{output_name}.mp4"
imageio.mimsave(output_path, video, fps=8)
print(f"Video saved: {{output_path}}")
'''
    
    title = f"video-gen-{output_name}"
    result = create_kernel(title, code, gpu=True)
    return result


# Test
if __name__ == "__main__":
    prompt = "Cinematic anime style, old war veteran sitting by campfire, dramatic orange firelight, dark moody atmosphere"
    result = submit_video_generation(prompt, "izuku-test")
    print(json.dumps(result, indent=2))
