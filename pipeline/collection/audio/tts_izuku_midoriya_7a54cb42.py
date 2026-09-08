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

text = """I’ve stood against monsters that shook the earth, but my hardest battle was always the quiet hour before dawn. When the air is cold and your own mind whispers every reason to break... conquer that silence, and no war will ever destroy you."""
speaker_idx = 0

print(f"Generating speech (speaker {speaker_idx})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("izuku_midoriya_7a54cb42.wav", audio, sample_rate)
print(f"Saved: izuku_midoriya_7a54cb42.wav")
print(f"Duration: {len(audio)/sample_rate:.1f}s")
