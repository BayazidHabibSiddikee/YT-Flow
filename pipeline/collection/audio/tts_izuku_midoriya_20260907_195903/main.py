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

text = """You don't lack capital; you lack a leverageable skill and the discipline to hunt.   Solve one painful problem for three people using pure sweat equity.   Let their cash flow fund your empire—not an investor's permission."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_20260907_195903.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_20260907_195903.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
