
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
prompt = """Cinematic izuku midoriya style, a warrior's greatest battle is not fought on the field, but in the silence of his own mind before the dawn, dramatic lighting, epic, 4k quality"""
result = pipe(prompt, num_frames=32, guidance_scale=7.5)
video = result.frames[0]

# Save as MP4
import imageio
imageio.mimsave("output.mp4", video, fps=8)
print("Video saved: output.mp4")
