
# Kaggle GPU Video Generation
# Model: modelscope/text-to-video-ms-1.7b

import torch
from diffusers import TextToVideoSDPipeline

print("Loading model: modelscope/text-to-video-ms-1.7b")
pipe = TextToVideoSDPipeline.from_pretrained(
    "modelscope/text-to-video-ms-1.7b",
    torch_dtype=torch.float16,
)
pipe.to("cuda")

print("Generating video...")
prompt = """Cinematic izuku midoriya style, the warrior who conquers himself is greater than one who conquers a thousand men in battle, dramatic lighting, epic, 4k quality"""
result = pipe(prompt, num_frames=32, guidance_scale=7.5)
video = result.frames[0]

# Save as MP4
import imageio
imageio.mimsave("output.mp4", video, fps=8)
print("Video saved: output.mp4")
