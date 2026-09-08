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

text = """I have watched men level cities with a single strike, only to be broken by their own wrath. Striking down a thousand enemies is simple... the true victory is mastering the storm inside your own heart."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_aa5cffae.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_aa5cffae.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
