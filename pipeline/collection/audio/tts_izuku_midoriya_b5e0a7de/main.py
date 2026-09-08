#!/usr/bin/env python3
"""VibeVoice TTS — Kaggle GPU Notebook"""
import torch
import soundfile as sf
from transformers import AutoModelForCausalLM

print("Loading VibeVoice-Realtime-0.5B...")
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/VibeVoice-Realtime-0.5B",
    torch_dtype=torch.float16,
    device_map="auto",
)

text = """I’ve held power that could shatter cities, yet the fiercest war I ever fought was behind my own eyes. To defeat a thousand enemies in the mud is easy. To conquer the storm inside your own heart... that is true strength."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_b5e0a7de.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_b5e0a7de.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
