#!/usr/bin/env python3
"""Marin Pipeline — Main Orchestrator (Hermes Controller)

Full pipeline:
1. Generate story/advice (LangChain + RAG)
2. Generate TTS audio (Kaggle Vibe Voice / edge-tts)
3. Generate images (Pollinations AI)
4. Create video (FFmpeg)
5. Queue for editor (opencode/claude/cline)

Usage:
  python pipeline.py index
  python pipeline.py short izuku_midoriya "the night before the battle"
  python pipeline.py long gym_mentality "ego kills progress"
  python pipeline.py download "https://youtube.com/watch?v=..." izuku_midoriya
  python pipeline.py status
"""

import json
import sys
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from config import (
    NICHES, COLLECTION_DIR, AUDIO_COLLECTION, IMAGES_COLLECTION,
    VIDEO_COLLECTION, SHORTS_OUTPUT, LONGS_OUTPUT, EDITOR_DIR,
    POLLINATIONS_URL,
)
from rag.rag_engine import RAGManager
from generator import StoryGenerator
from tts import VibeVoiceTTS
from images import ImageGenerator
from video_combiner import VideoCombiner
from video_minimax import MiniMaxH3
from video_hf import VideoGenManager
from youtube_downloader import YouTubeDownloader


class MarinPipeline:
    """Main pipeline — Hermes-controlled."""

    def __init__(self):
        print("=" * 60)
        print("  MARIN VIDEO PIPELINE — Hermes Controller")
        print("=" * 60)

        self.rag = RAGManager(NICHES)
        self.generator = StoryGenerator(self.rag)
        self.tts = VibeVoiceTTS()
        self.img_gen = ImageGenerator()
        self.combiner = VideoCombiner()
        self.minimax = MiniMaxH3()
        self.video_gen = VideoGenManager()
        self.downloader = YouTubeDownloader()

        for d in [AUDIO_COLLECTION, IMAGES_COLLECTION, VIDEO_COLLECTION,
                  SHORTS_OUTPUT, LONGS_OUTPUT, EDITOR_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        self.log_path = EDITOR_DIR / "pipeline_log.jsonl"
        print("[Pipeline] Ready\n")

    # ── RAG Index ────────────────────────────────────────────────────────────

    def index_knowledge(self) -> dict:
        print("\n[Pipeline] Indexing RAG knowledge bases...")
        results = self.rag.index_all()
        for niche, count in results.items():
            print(f"  {niche}: {count} chunks")
        return results

    # ── Image Generation ─────────────────────────────────────────────────────

    def _generate_images(self, niche_id: str, topic: str, story_text: str, count: int = 3) -> list[Path]:
        """Generate AI scene images."""
        return self.img_gen.generate(niche_id, topic, story_text, count)

    # ── Short Pipeline ───────────────────────────────────────────────────────

    def generate_short(self, niche_id: str, topic: str) -> dict:
        """Generate SHORT video: text → TTS → images → FFmpeg → editor."""
        print(f"\n{'='*60}")
        print(f"  SHORT: {niche_id} — {topic}")
        print(f"{'='*60}")

        # 1. Generate text
        print("[1/4] Generating story...")
        content = self.generator.generate(niche_id, topic, content_type="short")
        print(f"  Text: {len(content['text'])} chars")

        # 2. TTS
        print("[2/4] Generating voice...")
        audio_path = self.tts.generate(content["text"], niche_id)

        # 3. Images
        print("[3/4] Generating images...")
        images = self._generate_images(niche_id, topic, content["text"])
        print(f"  Images: {len(images)}")

        # 4. Video
        print("[4/4] Creating video...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = SHORTS_OUTPUT / f"{niche_id}_{ts}.mp4"

        # Try: HF/Kaggle AI video → MiniMax → FFmpeg fallback
        video_created = False

        # 1. HuggingFace free inference / Kaggle GPU
        if not video_created:
            try:
                print("[4/4] Trying HF/Kaggle video generation...")
                prompt = f"Cinematic {niche_id.replace('_', ' ')} style, {topic}, dramatic lighting, epic, 4k quality"
                self.video_gen.generate(prompt, video_path)
                if video_path.exists() and video_path.stat().st_size > 10000:
                    video_created = True
            except Exception as e:
                print(f"  HF/Kaggle failed: {e}")

        # 2. MiniMax H3
        if not video_created and self.minimax.available:
            try:
                print("[4/4] Trying MiniMax H3...")
                prompt = f"Cinematic {niche_id.replace('_', ' ')} style, {topic}, dramatic lighting, epic"
                self.minimax.text_to_video(prompt, video_path, duration=5, ratio="9:16")
                video_created = True
            except Exception as e:
                print(f"  MiniMax failed: {e}")

        # 3. FFmpeg fallback (images + audio)
        if not video_created:
            if images:
                print("[4/4] Using FFmpeg (images + audio)...")
                self.combiner.images_audio_to_video(audio_path, images, video_path, text=content["text"])
                video_created = True
            else:
                print("  WARNING: No images, audio-only")
                import shutil
                shutil.copy2(audio_path, SHORTS_OUTPUT / f"{niche_id}_{ts}.mp3")

        # Queue for editor
        self._queue_editor(content, video_path, audio_path)

        result = {
            "status": "done", "type": "short", "niche": niche_id,
            "topic": topic, "text": content["text"],
            "audio": str(audio_path), "video": str(video_path),
            "timestamp": ts,
        }
        self._log(result)
        print(f"\n  DONE → {video_path}")
        return result

    # ── Long Pipeline ────────────────────────────────────────────────────────

    def generate_long(self, niche_id: str, topic: str) -> dict:
        """Generate LONG video: text → TTS → images/video → FFmpeg → editor."""
        print(f"\n{'='*60}")
        print(f"  LONG: {niche_id} — {topic}")
        print(f"{'='*60}")

        # 1. Generate detailed text
        print("[1/4] Generating long-form content...")
        content = self.generator.generate(niche_id, topic, content_type="long")
        print(f"  Text: {len(content['text'])} chars")

        # 2. TTS
        print("[2/4] Generating voice...")
        audio_path = self.tts.generate(content["text"], niche_id)

        # 3. Images (more for longs)
        print("[3/4] Generating images...")
        images = self._generate_images(niche_id, topic, content["text"], count=10)
        print(f"  Images: {len(images)}")

        # 4. Video
        print("[4/4] Creating video...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = LONGS_OUTPUT / f"{niche_id}_long_{ts}.mp4"

        # Try: HF/Kaggle AI video → MiniMax → FFmpeg fallback
        video_created = False

        # 1. HuggingFace free inference / Kaggle GPU
        if not video_created:
            try:
                print("[4/4] Trying HF/Kaggle video generation...")
                prompt = f"Cinematic {niche_id.replace('_', ' ')} long-form storytelling, {topic}, dramatic, 4k"
                self.video_gen.generate(prompt, video_path)
                if video_path.exists() and video_path.stat().st_size > 10000:
                    video_created = True
            except Exception as e:
                print(f"  HF/Kaggle failed: {e}")

        # 2. MiniMax H3
        if not video_created and self.minimax.available:
            try:
                print("[4/4] Trying MiniMax H3...")
                prompt = f"Cinematic {niche_id.replace('_', ' ')} long-form, {topic}, dramatic storytelling"
                self.minimax.text_to_video(prompt, video_path, duration=10, ratio="16:9")
                video_created = True
            except Exception as e:
                print(f"  MiniMax failed: {e}")

        # 3. FFmpeg fallback (images + audio)
        if not video_created:
            if images:
                print("[4/4] Using FFmpeg (images + audio)...")
                self.combiner.images_audio_to_video(audio_path, images, video_path, text=content["text"], duration_per_image=6.0)
                video_created = True
            else:
                print("  WARNING: No images, audio-only")
                import shutil
                shutil.copy2(audio_path, LONGS_OUTPUT / f"{niche_id}_long_{ts}.mp3")

        self._queue_editor(content, video_path, audio_path)

        result = {
            "status": "done", "type": "short", "niche": niche_id,
            "topic": topic, "text": content["text"],
            "audio": str(audio_path), "video": str(video_path),
            "timestamp": ts,
        }
        self._log(result)
        print(f"\n  DONE → {video_path}")
        return result

    # ── YouTube ──────────────────────────────────────────────────────────────

    def download_youtube(self, url: str, niche_id: str) -> Path:
        """Download YouTube video to collection."""
        out = COLLECTION_DIR / "video" / niche_id
        return self.downloader.download_video(url, out)

    def download_channel(self, channel_url: str, niche_id: str, max_videos: int = 5):
        out = COLLECTION_DIR / "video" / niche_id
        return self.downloader.download_channel(channel_url, out, max_videos)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _queue_editor(self, content: dict, video_path: Path, audio_path: Path):
        queue_file = EDITOR_DIR / "edit_queue.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "niche": content["niche"],
            "topic": content["topic"],
            "text": content["text"],
            "video": str(video_path),
            "audio": str(audio_path),
            "status": "pending_edit",
        }
        with open(queue_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log(self, result: dict):
        with open(self.log_path, "a") as f:
            f.write(json.dumps(result) + "\n")

    def status(self) -> dict:
        return {
            "collection": {
                "audio": len(list(AUDIO_COLLECTION.glob("*.*"))),
                "images": len(list(IMAGES_COLLECTION.glob("*.*"))),
                "video": len(list(VIDEO_COLLECTION.glob("*.*"))),
            },
            "output": {
                "shorts": len(list(SHORTS_OUTPUT.glob("*.mp4"))),
                "longs": len(list(LONGS_OUTPUT.glob("*.mp4"))),
            },
            "editor_queue": sum(1 for _ in open(EDITOR_DIR / "edit_queue.jsonl"))
            if (EDITOR_DIR / "edit_queue.jsonl").exists() else 0,
            "niches": list(NICHES.keys()),
        }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Marin Video Pipeline")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("index", help="Index RAG knowledge bases")
    sub.add_parser("status", help="Show pipeline status")

    gen_s = sub.add_parser("short", help="Generate short video")
    gen_s.add_argument("niche", choices=list(NICHES.keys()))
    gen_s.add_argument("topic", nargs="+")

    gen_l = sub.add_parser("long", help="Generate long video")
    gen_l.add_argument("niche", choices=list(NICHES.keys()))
    gen_l.add_argument("topic", nargs="+")

    dl = sub.add_parser("download", help="Download YouTube video")
    dl.add_argument("url")
    dl.add_argument("niche", choices=list(NICHES.keys()))

    args = parser.parse_args()
    pipeline = MarinPipeline()

    if args.command == "index":
        pipeline.index_knowledge()
    elif args.command == "short":
        pipeline.generate_short(args.niche, " ".join(args.topic))
    elif args.command == "long":
        pipeline.generate_long(args.niche, " ".join(args.topic))
    elif args.command == "download":
        pipeline.download_youtube(args.url, args.niche)
    elif args.command == "status":
        print(json.dumps(pipeline.status(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
