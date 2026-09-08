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

text = """I’ve seen men level whole cities, only to be destroyed by the darkness in their own hearts.  Defeating a thousand enemies on the battlefield means nothing if you lose the war inside yourself.  Master your own soul, kid... that is where true strength begins."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_b2152ba7.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_b2152ba7.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
