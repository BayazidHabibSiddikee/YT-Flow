#!/usr/bin/env python3
"""Orchestrator — Full multi-agent pipeline.

Flow:
1. IZUKU generates idea (or user provides topic)
2. DIRECTOR reviews and approves/revolves
3. VIDEO PRODUCER creates TTS + images + video
4. QUALITY CHECKER rates the video
5. PUBLISHER prepares YouTube + social uploads
6. IZUKU writes social posts
7. Final output: video + captions + upload metadata

Usage:
    python orchestrator.py run "how to start a business"
    python orchestrator.py run "discipline over motivation" --type short
    python orchestrator.py batch topics.txt
    python orchestrator.py status
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import NICHES, SHORTS_OUTPUT, LONGS_OUTPUT
from pipeline.generator import StoryGenerator
from pipeline.tts import VibeVoiceTTS
from pipeline.images import ImageGenerator
from pipeline.video_combiner import VideoCombiner
from pipeline.rag.rag_engine import RAGManager

from pipeline.agents.director import DirectorAgent
from pipeline.agents.quality_checker import QualityChecker
from pipeline.agents.publisher import PublisherAgent
from pipeline.agents.social_writer import SocialWriter


class Orchestrator:
    """Multi-agent pipeline orchestrator."""

    def __init__(self):
        print("=" * 60)
        print("  SOCIO BUSINESS — Multi-Agent Pipeline")
        print("=" * 60)

        # Core pipeline
        self.rag = RAGManager(NICHES)
        self.generator = StoryGenerator(self.rag)
        self.tts = VibeVoiceTTS()
        self.img_gen = ImageGenerator()
        self.combiner = VideoCombiner()

        # Agents
        self.director = DirectorAgent()
        self.quality = QualityChecker()
        self.publisher = PublisherAgent()
        self.social_writer = SocialWriter()

        # State
        self.state_dir = Path("output/state")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        print("[Orchestrator] Ready\n")

    def run(self, topic: str, niche: str = "izuku_midoriya", content_type: str = "short") -> dict:
        """Run full pipeline for one topic."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{niche}_{ts}"

        print(f"\n{'='*60}")
        print(f"  RUN: {run_id}")
        print(f"  Topic: {topic}")
        print(f"{'='*60}\n")

        result = {"run_id": run_id, "topic": topic, "niche": niche, "stages": {}}

        # ── STAGE 1: Generate Content ────────────────────────────────────────
        print("━" * 40)
        print("  STAGE 1: Izuku generates content")
        print("━" * 40)

        content = self.generator.generate(niche, topic, content_type)
        result["stages"]["content"] = {
            "text": content["text"],
            "sources": content.get("rag_sources", []),
        }
        print(f"  Generated: {len(content['text'])} chars\n")

        # ── STAGE 2: Director Reviews ────────────────────────────────────────
        print("━" * 40)
        print("  STAGE 2: Director reviews")
        print("━" * 40)

        review = self.director.review({
            "topic": topic,
            "text": content["text"],
            "niche": niche,
            "content_type": content_type,
        })
        result["stages"]["director"] = review

        verdict = review.get("verdict", "REJECT")
        if verdict == "REJECT":
            print(f"\n  Director REJECTED: {review.get('reasoning', 'No reason')}")
            result["status"] = "rejected"
            self._save_state(result)
            return result

        # Use Director's suggestions if REVISE
        if verdict == "REVISE":
            print(f"\n  Director REVISED: {review.get('changes_if_revise', '')}")
            # Regenerate with director's notes
            content = self.generator.generate(
                niche, topic, content_type,
                instructions=review.get("changes_if_revise", ""),
            )
            result["stages"]["content"]["text"] = content["text"]

        print(f"\n  Director approved (score: {review.get('score', '?')}/10)")
        print(f"  Hook: {review.get('hook', 'N/A')}\n")

        # ── STAGE 3: Video Production ────────────────────────────────────────
        print("━" * 40)
        print("  STAGE 3: Video production")
        print("━" * 40)

        # 3a: TTS
        print("\n  [3a] Generating voice...")
        audio_path = self.tts.generate(content["text"], niche, filename=f"{run_id}.wav")

        # 3b: Images (use Director's scene descriptions)
        print("\n  [3b] Generating images...")
        scene_prompts = review.get("images", [topic])
        images = []
        for i, scene in enumerate(scene_prompts[:5]):
            img_path = Path(f"output/images/{run_id}_scene_{i}.jpg")
            img_path.parent.mkdir(parents=True, exist_ok=True)
            if not img_path.exists():
                try:
                    self.img_gen.generate_pollinations(
                        f"{review.get('style', 'cinematic')}, {scene}",
                        img_path,
                        seed=hash(f"{topic}{i}") % 10000,
                    )
                    images.append(img_path)
                except Exception as e:
                    print(f"    Image {i} failed: {e}")
            else:
                images.append(img_path)
        print(f"  Images: {len(images)}")

        # 3c: Create video
        print("\n  [3c] Creating video...")
        if content_type == "short":
            video_path = SHORTS_OUTPUT / f"{run_id}.mp4"
        else:
            video_path = LONGS_OUTPUT / f"{run_id}_long.mp4"

        if images:
            self.combiner.images_audio_to_video(
                audio_path, images, video_path, text=content["text"]
            )
        else:
            # Audio-only
            import shutil
            shutil.copy2(audio_path, video_path.with_suffix(".mp3"))
            video_path = video_path.with_suffix(".mp3")

        result["stages"]["video"] = {
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "images": [str(i) for i in images],
        }
        print(f"  Video: {video_path}\n")

        # ── STAGE 4: Quality Check ───────────────────────────────────────────
        print("━" * 40)
        print("  STAGE 4: Quality check")
        print("━" * 40)

        quality = self.quality.check({
            "video_path": str(video_path),
            "text": content["text"],
            "topic": topic,
            "niche": niche,
            "audio_path": str(audio_path),
            "images": [str(i) for i in images],
        })
        result["stages"]["quality"] = quality

        if quality.get("verdict") == "REJECT":
            print(f"\n  Quality REJECTED: {quality.get('reasoning', '')}")
            result["status"] = "quality_rejected"
            self._save_state(result)
            return result

        if quality.get("verdict") == "EDIT_NEEDED":
            print(f"\n  Quality: EDIT NEEDED — {quality.get('issues', [])}")
            # Continue but flag for review

        print(f"\n  Quality: {quality.get('overall_score', 0)}/10\n")

        # ── STAGE 5: Publish Preparation ─────────────────────────────────────
        print("━" * 40)
        print("  STAGE 5: Publish preparation")
        print("━" * 40)

        # 5a: Publisher prepares upload package
        upload_meta = self.publisher.prepare_upload({
            "topic": topic,
            "text": content["text"],
            "niche": niche,
            "content_type": content_type,
        })
        result["stages"]["upload_meta"] = upload_meta

        # 5b: Save YouTube metadata
        self.publisher.upload_to_youtube(video_path, upload_meta)

        # 5c: Save social captions
        caption_path = self.publisher.save_social_captions(upload_meta, {
            "topic": topic,
            "text": content["text"],
        })
        result["stages"]["captions_path"] = str(caption_path)

        # ── STAGE 6: Social Posts ────────────────────────────────────────────
        print("━" * 40)
        print("  STAGE 6: Izuku writes social posts")
        print("━" * 40)

        posts = self.social_writer.write_posts({
            "topic": topic,
            "text": content["text"],
            "niche": niche,
        })
        post_path = self.social_writer.save_posts(posts, {"topic": topic})
        result["stages"]["social_posts"] = str(post_path)

        # ── DONE ─────────────────────────────────────────────────────────────
        result["status"] = "complete"
        result["video_path"] = str(video_path)
        self._save_state(result)

        print(f"\n{'='*60}")
        print(f"  COMPLETE: {run_id}")
        print(f"  Video: {video_path}")
        print(f"  Captions: {caption_path}")
        print(f"  Posts: {post_path}")
        print(f"{'='*60}\n")

        return result

    def batch(self, topics_file: str, niche: str = "izuku_midoriya"):
        """Run pipeline for multiple topics from a file."""
        topics_path = Path(topics_file)
        if not topics_path.exists():
            print(f"File not found: {topics_file}")
            return

        topics = [line.strip() for line in topics_path.read_text().splitlines() if line.strip()]
        print(f"\nBatch: {len(topics)} topics from {topics_file}\n")

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] {topic}")
            result = self.run(topic, niche)
            results.append(result)

        # Summary
        print(f"\n{'='*60}")
        print(f"  BATCH COMPLETE: {len(results)} videos")
        print(f"  Successful: {sum(1 for r in results if r['status'] == 'complete')}")
        print(f"  Rejected: {sum(1 for r in results if 'reject' in r['status'])}")
        print(f"{'='*60}")

    def status(self) -> dict:
        """Show pipeline status."""
        state_files = list(self.state_dir.glob("*.json"))
        complete = sum(1 for f in state_files
                      if json.loads(f.read_text()).get("status") == "complete")
        return {
            "total_runs": len(state_files),
            "complete": complete,
            "pending": len(state_files) - complete,
        }

    def _save_state(self, result: dict):
        """Save run state."""
        path = self.state_dir / f"{result['run_id']}.json"
        path.write_text(json.dumps(result, indent=2, default=str))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Socio Business Multi-Agent Pipeline")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="Run full pipeline for a topic")
    run_cmd.add_argument("topic", nargs="+")
    run_cmd.add_argument("--niche", default="izuku_midoriya")
    run_cmd.add_argument("--type", default="short", choices=["short", "long"])

    batch_cmd = sub.add_parser("batch", help="Run pipeline for multiple topics")
    batch_cmd.add_argument("file", help="Text file with one topic per line")
    batch_cmd.add_argument("--niche", default="izuku_midoriya")

    sub.add_parser("status", help="Show pipeline status")

    args = parser.parse_args()
    orch = Orchestrator()

    if args.command == "run":
        orch.run(" ".join(args.topic), args.niche, args.type)
    elif args.command == "batch":
        orch.batch(args.file, args.niche)
    elif args.command == "status":
        print(json.dumps(orch.status(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
