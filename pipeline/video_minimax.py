#!/usr/bin/env python3
"""Marin Pipeline — MiniMax H3 Video Generation

Generates AI videos via MiniMax H3 API.
Supports: text-to-video, image-to-video, reference-to-video.
"""

import time
import requests
from pathlib import Path

from config import MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL


class MiniMaxH3:
    """MiniMax H3 video generation client."""

    def __init__(self):
        self.api_key = MINIMAX_API_KEY
        self.base_url = MINIMAX_BASE_URL
        self.model = MINIMAX_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.available = bool(self.api_key)
        if not self.available:
            print("[MiniMax] No API key — using fallback video generation")

    def text_to_video(
        self,
        prompt: str,
        output_path: Path,
        duration: int = 5,
        resolution: str = "2K",
        ratio: str = "9:16",
    ) -> Path:
        """Generate video from text prompt."""
        if not self.available:
            raise RuntimeError("MiniMax API key not configured")

        url = f"{self.base_url}/v2/video_generation"
        payload = {
            "model": self.model,
            "content": [{"type": "text", "text": prompt}],
            "duration": duration,
            "resolution": resolution,
            "ratio": ratio,
        }

        print(f"[MiniMax] Submitting text-to-video task...")
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"[MiniMax] Task ID: {task_id}")

        # Poll for completion
        video_url = self._poll_task(task_id)
        return self._download(video_url, output_path)

    def image_to_video(
        self,
        image_url: str,
        prompt: str,
        output_path: Path,
        duration: int = 5,
        role: str = "first_frame",
    ) -> Path:
        """Generate video from image + text prompt."""
        if not self.available:
            raise RuntimeError("MiniMax API key not configured")

        url = f"{self.base_url}/v2/video_generation"
        payload = {
            "model": self.model,
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}, "role": role},
            ],
            "duration": duration,
            "resolution": "2K",
        }

        print(f"[MiniMax] Submitting image-to-video task...")
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"[MiniMax] Task ID: {task_id}")

        video_url = self._poll_task(task_id)
        return self._download(video_url, output_path)

    def reference_to_video(
        self,
        prompt: str,
        output_path: Path,
        image_urls: list[str] = None,
        video_urls: list[str] = None,
        audio_urls: list[str] = None,
        duration: int = 5,
    ) -> Path:
        """Generate video from reference inputs (images, videos, audio)."""
        if not self.available:
            raise RuntimeError("MiniMax API key not configured")

        content = [{"type": "text", "text": prompt}]

        for url in (image_urls or []):
            content.append({"type": "image_url", "image_url": {"url": url}, "role": "reference_image"})
        for url in (video_urls or []):
            content.append({"type": "video_url", "video_url": {"url": url}, "role": "reference_video"})
        for url in (audio_urls or []):
            content.append({"type": "audio_url", "audio_url": {"url": url}, "role": "reference_audio"})

        url = f"{self.base_url}/v2/video_generation"
        payload = {"model": self.model, "content": content, "duration": duration, "resolution": "2K"}

        print(f"[MiniMax] Submitting reference-to-video task...")
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"[MiniMax] Task ID: {task_id}")

        video_url = self._poll_task(task_id)
        return self._download(video_url, output_path)

    def _poll_task(self, task_id: str, max_wait: int = 600) -> str:
        """Poll task status until complete. Returns video download URL."""
        url = f"{self.base_url}/v2/query/video_generation/{task_id}"
        start = time.time()

        while time.time() - start < max_wait:
            time.sleep(10)
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            task = resp.json()["task"]
            status = task["status"]
            print(f"[MiniMax] Status: {status}")

            if status == "succeeded":
                return task["content"]["url"]
            if status in ("failed", "cancelled"):
                raise RuntimeError(f"Task failed: {task.get('error', 'unknown')}")

        raise TimeoutError(f"Task {task_id} timed out after {max_wait}s")

    def _download(self, url: str, output_path: Path) -> Path:
        """Download video from URL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[MiniMax] Downloading video...")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        print(f"[MiniMax] Saved: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
        return output_path
