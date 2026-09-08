#!/usr/bin/env python3
"""Marin Pipeline — YouTube Downloader

Downloads videos/audio from YouTube for content repurposing
and RAG knowledge base population.
"""

import json
import subprocess
from pathlib import Path

from config import COLLECTION_DIR


class YouTubeDownloader:
    """yt-dlp based downloader."""

    def __init__(self):
        self.ytdlp = "yt-dlp"

    def download_video(self, url: str, output_dir: Path, quality: str = "best[height<=1080]") -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        template = str(output_dir / "%(title)s.%(ext)s")

        cmd = [
            self.ytdlp, "-f", quality, "--merge-output-format", "mp4",
            "-o", template, "--no-playlist", "--write-info-json", url,
        ]
        print(f"[yt-dlp] Downloading: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"Download failed: {result.stderr[:300]}")

        mp4s = sorted(output_dir.glob("*.mp4"), key=lambda x: x.stat().st_mtime)
        return mp4s[-1] if mp4s else None

    def download_audio(self, url: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ytdlp, "-f", "bestaudio", "--extract-audio",
            "--audio-format", "mp3", "--audio-quality", "0",
            "-o", str(output_dir / "%(title)s.%(ext)s"),
            "--no-playlist", url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"Audio download failed: {result.stderr[:300]}")

        mp3s = sorted(output_dir.glob("*.mp3"), key=lambda x: x.stat().st_mtime)
        return mp3s[-1] if mp3s else None

    def download_subtitles(self, url: str, output_dir: Path, lang: str = "en") -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ytdlp, "--write-auto-sub", "--sub-lang", lang,
            "--skip-download", "-o", str(output_dir / "%(title)s.%(ext)s"), url,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        vtt = list(output_dir.glob("*.vtt"))
        return vtt[0] if vtt else None

    def download_channel(self, channel_url: str, output_dir: Path, max_videos: int = 10) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [self.ytdlp, "--flat-playlist", "--playlist-end", str(max_videos), "-j", channel_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return []

        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                info = json.loads(line)
                video_url = f"https://www.youtube.com/watch?v={info.get('id', '')}"
                path = self.download_video(video_url, output_dir, quality="best[height<=720]")
                if path:
                    videos.append(path)
            except Exception:
                pass
        return videos
