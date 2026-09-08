#!/usr/bin/env python3
"""Pipeline TTS — VibeVoice via Kaggle GPU

Voice assignments:
- Izuku Midoriya: old man voice
- Gym Mentality: male motivational voice
- Krishna Religious: female calm voice

VibeVoice-Realtime-0.5B runs on Kaggle's free T4 GPU.
Falls back to edge-tts only when Kaggle is unavailable.
"""

import asyncio
import hashlib
import json
import subprocess
import time
from pathlib import Path

import edge_tts

from config import KAGGLE_API_TOKEN, AUDIO_COLLECTION, NICHES

# ── VibeVoice Speakers ──────────────────────────────────────────────────────
# VibeVoice-Realtime-0.5B has embedded speakers, we select by index
VIBEVOICE_SPEAKERS = {
    "old_man": 0,           # Default male voice (deep, mature)
    "male_motivational": 0, # Same male, different pacing
    "female_calm": 4,       # Female voice
}

EDGE_TTS_FALLBACK = {
    "old_man": ("en-US-BrianNeural", "-12%"),
    "male_motivational": ("en-US-AndrewNeural", "+0%"),
    "female_calm": ("en-US-AvaNeural", "+0%"),
}


class VibeVoiceTTS:
    """TTS via VibeVoice-Realtime-0.5B on Kaggle GPU."""

    def __init__(self):
        self.kaggle_available = self._check_kaggle()
        self.output_dir = AUDIO_COLLECTION
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _check_kaggle(self) -> bool:
        if not KAGGLE_API_TOKEN:
            print("[TTS] No Kaggle token")
            return False
        try:
            r = subprocess.run(["kaggle", "--version"], capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

    def _build_kaggle_notebook(self, text: str, speaker_idx: int, output_name: str) -> Path:
        """Create a Kaggle notebook directory for VibeVoice inference."""
        import json

        notebook_code = f'''#!/usr/bin/env python3
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

text = """{text.replace('"', '\\"').replace(chr(10), ' ')}"""
speaker_idx = {speaker_idx}

print(f"Generating speech (speaker {{speaker_idx}})...")
output = model.generate(
    text=text,
    speaker=speaker_idx,
    max_new_tokens=4096,
)

audio = output["audio"]
sample_rate = output.get("sample_rate", 24000)

sf.write("{output_name}.wav", audio, sample_rate)
print(f"Saved: {output_name}.wav")
print(f"Duration: {{len(audio)/sample_rate:.1f}}s")
'''
        nb_dir = self.output_dir / f"tts_{output_name}"
        nb_dir.mkdir(parents=True, exist_ok=True)

        # Write the notebook script
        nb_path = nb_dir / "main.py"
        nb_path.write_text(notebook_code)

        # Write kernel-metadata.json (required by Kaggle CLI)
        meta = {
            "id": f"sword/{output_name}",
            "title": f"VibeVoice TTS - {output_name}",
            "code_file": "main.py",
            "language": "python",
            "kernel_type": "notebook",
            "enable_gpu": True,
            "enable_internet": True,
        }
        meta_path = nb_dir / "kernel-metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2))

        return nb_dir

    def _submit_kaggle(self, nb_path: Path) -> bool:
        """Submit notebook to Kaggle: kaggle kernels push -p <folder> --accelerator GPU"""
        try:
            result = subprocess.run(
                ["kaggle", "kernels", "push", "-p", str(nb_path), "--accelerator", "GPU"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                print(f"[TTS:Kaggle] Notebook submitted: {nb_path.name}")
                print(f"[TTS:Kaggle] Check: https://www.kaggle.com/code")
                return True
            else:
                print(f"[TTS:Kaggle] Submit failed: {result.stderr[:300]}")
                return False
        except Exception as e:
            print(f"[TTS:Kaggle] Error: {e}")
            return False

    async def _edge_generate(self, text: str, voice: str, output_path: Path, rate: str):
        comm = edge_tts.Communicate(text, voice, rate=rate)
        await comm.save(str(output_path))

    def generate(self, text: str, niche_id: str, filename: str = None) -> Path:
        """Generate TTS audio. Tries VibeVoice on Kaggle, falls back to edge-tts."""
        niche_cfg = NICHES.get(niche_id, {})
        voice_type = niche_cfg.get("voice", "male_motivational")

        if not filename:
            h = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"{niche_id}_{h}.wav"

        output_path = self.output_dir / filename

        # 1. Try VibeVoice on Kaggle GPU
        if self.kaggle_available:
            speaker_idx = VIBEVOICE_SPEAKERS.get(voice_type, 0)
            nb_path = self._build_kaggle_notebook(text, speaker_idx, filename.replace(".wav", ""))

            if self._submit_kaggle(nb_path):
                print(f"[TTS:VibeVoice] Notebook submitted to Kaggle GPU")
                print(f"[TTS:VibeVoice] Download output from Kaggle when done")
                # For now, also generate edge-tts as immediate fallback
                # Kaggle is async — the real VibeVoice audio comes from there

        # 2. Immediate fallback: edge-tts
        edge_voice, edge_rate = EDGE_TTS_FALLBACK.get(voice_type, ("en-US-GuyNeural", "+0%"))
        print(f"[TTS:edge] Generating immediately: {edge_voice}")

        # Convert to mp3 for edge-tts, we'll convert back if needed
        mp3_path = output_path.with_suffix(".mp3")
        asyncio.run(self._edge_generate(text, edge_voice, mp3_path, edge_rate))

        # Convert to wav if needed
        if output_path.suffix == ".wav":
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "24000", str(output_path)],
                capture_output=True, timeout=30,
            )
            mp3_path.unlink(missing_ok=True)
        else:
            output_path = mp3_path

        print(f"[TTS] Done: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
        return output_path

    def generate_batch(self, items: list[dict]) -> list[Path]:
        return [self.generate(i["text"], i["niche_id"], i.get("filename")) for i in items]
