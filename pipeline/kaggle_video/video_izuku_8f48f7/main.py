
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
prompt = """Cinematic anime style, old war veteran sitting by campfire, ruined city in background, dramatic orange firelight, dark moody atmosphere, emotional, detailed, 4k quality. Scene: In the midst of chaos, there is also opportunity"""
video = pipe(
    prompt=prompt,
    num_frames=49,
    guidance_scale=6.0,
    num_inference_steps=50,
).frames[0]

# Save video
import imageio
output_path = "izuku_8f48f7.mp4"
imageio.mimsave(output_path, video, fps=8)
print(f"Video saved: {output_path}")
print(f"Duration: {len(video)/8:.1f}s")
