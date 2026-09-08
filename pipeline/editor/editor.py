#!/usr/bin/env python3
"""Marin Pipeline — AI Video Editor

Post-production: captions, cuts, transitions.
Designed to be called by opencode/claude/cline with bypass permission.
"""

import json
import subprocess
from pathlib import Path

from config import EDITOR_DIR, FFMPEG_PATH


class VideoEditor:
    """AI-assisted video editor for final polish."""

    def __init__(self):
        self.ffmpeg = FFMPEG_PATH
        self.queue_file = EDITOR_DIR / "edit_queue.jsonl"
        self.completed_file = EDITOR_DIR / "completed.jsonl"

    def get_pending(self) -> list[dict]:
        if not self.queue_file.exists():
            return []
        pending = []
        for line in self.queue_file.read_text().strip().split("\n"):
            if line:
                entry = json.loads(line)
                if entry.get("status") == "pending_edit":
                    pending.append(entry)
        return pending

    def add_captions(self, video_path: Path, text: str, output_path: Path = None) -> Path:
        """Generate SRT from text and burn into video."""
        if output_path is None:
            output_path = video_path.parent / f"captioned_{video_path.name}"

        srt_path = video_path.parent / f"{video_path.stem}.srt"
        self._text_to_srt(text, srt_path)

        style = (
            "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=50"
        )
        cmd = [
            self.ffmpeg, "-y", "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style='{style}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy", "-movflags", "+faststart", str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        srt_path.unlink(missing_ok=True)
        if result.returncode == 0:
            return output_path
        raise RuntimeError(f"Caption burn failed: {result.stderr[:300]}")

    def _text_to_srt(self, text: str, srt_path: Path, chars_per_line: int = 40):
        words = text.split()
        lines, current, cur_len = [], [], 0
        for word in words:
            if cur_len + len(word) + 1 > chars_per_line and current:
                lines.append(" ".join(current))
                current, cur_len = [word], len(word)
            else:
                current.append(word)
                cur_len += len(word) + 1
        if current:
            lines.append(" ".join(current))

        entries = []
        for i, line in enumerate(lines):
            start = i * 2.0
            end = start + 2.0
            entries.append(f"{i+1}\n{self._fmt(start)} --> {self._fmt(end)}\n{line}\n")
        srt_path.write_text("\n".join(entries))

    def _fmt(self, s: float) -> str:
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        ms = int((sec % 1) * 1000)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"

    def process_all_pending(self) -> list[dict]:
        results = []
        for entry in self.get_pending():
            try:
                video = Path(entry["video"])
                if not video.exists():
                    results.append({"status": "error", "message": "Video not found"})
                    continue
                if entry.get("text"):
                    video = self.add_captions(video, entry["text"])
                entry["status"] = "edited"
                entry["edited_video"] = str(video)
                self._complete(entry)
                results.append({"status": "success", "video": str(video)})
            except Exception as e:
                results.append({"status": "error", "message": str(e)})
        return results

    def _complete(self, entry: dict):
        if self.queue_file.exists():
            lines = self.queue_file.read_text().strip().split("\n")
            new = [l for l in lines if l and json.loads(l).get("timestamp") != entry.get("timestamp")]
            self.queue_file.write_text("\n".join(new) + "\n" if new else "")
        with open(self.completed_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
