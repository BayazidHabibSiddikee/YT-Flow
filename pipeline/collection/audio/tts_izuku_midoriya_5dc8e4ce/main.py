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

text = """I have seen men level cities, yet bleed to death from the war inside their own minds.  Defeating a thousand enemies is simple—the true hero is the one who tames his own heart.  Win that quiet battle first, child."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_5dc8e4ce.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_5dc8e4ce.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
