#!/usr/bin/env python3
"""Hybrid Orchestrator — Best of Both Worlds

Uses our custom RAG knowledge base + multi-agent directors for content strategy,
then delegates video production entirely to MoneyPrinterTurbo (stock footage,
proper TTS, BGM mixing, Ken Burns effects, subtitles).

Pipeline Flow:
  RAG Context → Director (strategy) → MPT Video Production → Publisher → Social Writer

KEY DESIGN: All LLM script generation happens inside MPT (its own LLM),
so we avoid Gemini rate limits and freellmapi auth issues.

Usage:
    python hybrid_orchestrator.py run "how to start a business" --type short
    python hybrid_orchestrator.py run "discipline over motivation" --type long
    python hybrid_orchestrator.py batch topics.txt
    python hybrid_orchestrator.py status
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import NICHES, SHORTS_OUTPUT, LONGS_OUTPUT, CHARACTER_DIR
from pipeline.rag.rag_engine import RAGManager

from pipeline.agents.director import DirectorAgent
from pipeline.agents.publisher import PublisherAgent
from pipeline.agents.social_writer import SocialWriter
from pipeline.agents.video_analyzer import VideoAnalyzer

# ── MoneyPrinterTurbo Configuration ─────────────────────────────────────────
MPT_DIR = Path(__file__).parent.parent / "tools" / "MoneyPrinterTurbo"
MPT_CLI = MPT_DIR / "cli.py"

# Voice mapping per niche — optimized for each character
VOICE_MAP = {
    "izuku_midoriya": "en-US-ChristopherNeural",  # Confident, authoritative
    "gym_mentality": "en-US-AndrewNeural",        # Motivational, energetic
    "krishna_religious": "en-US-AvaNeural",        # Calm, soothing female
}

# Duration targets based on content type
SHORTS_PARAGRAPHS = 5   # ~30-45s target (5 clips x 5s + overhead)
LONGS_PARAGRAPHS = 8    # ~60-90s target (8 clips x 5s + overhead)


class HybridOrchestrator:
    """Multi-agent pipeline with MoneyPrinterTurbo video production."""

    def __init__(self):
        print("=" * 60)
        print("  SOCIO BUSINESS — HYBRID ORCHESTRATOR")
        print("  (RAG + MPT Hybrid Pipeline)")
        print("=" * 60)

        # Core pipeline
        self.rag = RAGManager(NICHES)
        self.director = DirectorAgent()
        self.publisher = PublisherAgent()
        self.social_writer = SocialWriter()
        self.video_analyzer = VideoAnalyzer()

        # State — match original pipeline location
        self.state_dir = Path(__file__).parent / "output" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        print("[HybridOrchestrator] Ready\n")

    def _get_voice(self, niche_id: str) -> str:
        return VOICE_MAP.get(niche_id, "en-US-ChristopherNeural")

    def _build_system_prompt(self, niche: str, rag_context: str) -> str:
        """Build MPT's custom system prompt combining character persona + RAG."""
        niche_cfg = NICHES.get(niche, {})
        char_name = niche_cfg.get("name", "wealthy polymath entrepreneur")

        # Get character system prompt from generator if available
        character_intro = f"""You are writing in the voice of {char_name} — a wealthy polymath entrepreneur, strategic thinker, and deep reader of human nature. You speak from lived experience, not theory. Your tone is calm, direct, and occasionally provocative. You blend business acumen with spiritual wisdom and psychological insight.

FORMAT CONSTRAINTS:
- SHORT format: 4-5 substantial paragraphs, ~20-35 words each
- LONG format: 7-8 substantial paragraphs, ~30-40 words each
- Start with a hook that grabs attention immediately

HUMAN-LIKE WRITING RULES:
- NEVER preach or summarize the moral. Show, don't tell. Let the viewer connect the dots.
- Include specific sensory details: the smell of rain on concrete, the weight of silence in a room, the taste of bitter coffee at dawn
- Mix sentence lengths aggressively: fragment. Then a long flowing sentence that builds. Then another short punch.
- Use at least one metaphor or simile per paragraph, but make it earned, not decorative
- Name real-feeling people: "my old trainer Raj", "Sarah across the desk" — never generic "you"
- Admit uncertainty sometimes: "I'm not sure I ever figured this out completely..."
- Avoid meta-phrases: "here's what I learned", "the lesson is", "remember that", "key takeaway"
- End on an image, a question, or a moment — never a recap or summary
- Write like you're sitting across from someone at 2am, not standing at a podium"""

        rag_section = f"\n\nRELEVANT KNOWLEDGE (use these insights):\n{rag_context}" if rag_context else ""

        return character_intro + rag_section

    def _generate_script_mpt(self, niche: str, topic: str, content_type: str, instructions: str = "") -> dict:
        """Generate a well-structured script using MPT's LLM with RAG context.

        Returns dict with script text and metadata.
        Uses MPT's internal LLM to avoid rate limits on our endpoints.
        """
        # Get RAG context
        query = f"{topic} {instructions}".strip()
        rag_results = self.rag.retrieve(niche, query, k=5)
        rag_context = "\n\n".join(
            [f"[Source: {r['metadata'].get('source', 'unknown')}]\n{r['text']}" for r in rag_results]
        ) if rag_results else "No specific context found. Use your best judgment."

        system_prompt = self._build_system_prompt(niche, rag_context)
        paragraph_count = SHORTS_PARAGRAPHS if content_type == "short" else LONGS_PARAGRAPHS

        # Run MPT script generation only (stop at script stage)
        cmd = [
            sys.executable, str(MPT_CLI),
            "--video-subject", topic,
            "--video-language", "en-US",
            "--paragraph-number", str(paragraph_count),
            "--custom-system-prompt", system_prompt,
            "--stop-at", "script",
        ]

        if instructions:
            cmd.extend(["--video-script-prompt", instructions])

        print(f"\n  [MPT Script] Generating with RAG context ({len(rag_results)} sources)...")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                cwd=str(MPT_DIR), env=env,
            )

            if result.returncode != 0:
                print(f"  [MPT Script] Error: {result.stderr[-300:]}")
                # Fallback: generate simple script locally
                return self._fallback_script(topic, content_type, instructions)

            # Extract JSON from potentially noisy output (ANSI codes, logs, etc.)
            import re
            # Strip ANSI color codes first
            cleaned = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
            # Find last JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}$', cleaned, re.DOTALL)
            if json_match:
                try:
                    output = json.loads(json_match.group())
                except json.JSONDecodeError:
                    output = None
            else:
                output = None

            if output is not None and "task_id" in output:
                script = output.get("result", {}).get("script", "")
                if script:
                    # Post-process: ensure adequate paragraphs but not too long
                    script = self._trim_script(script, content_type)
                    print(f"  [MPT Script] Generated: {len(script)} chars, {len(script.split())} words")
                    return {"script": script, "sources": [r['metadata'].get('source', '') for r in rag_results]}

            return self._fallback_script(topic, content_type, instructions)

        except subprocess.TimeoutExpired:
            return self._fallback_script(topic, content_type, instructions)
        except Exception as e:
            print(f"  [MPT Script] Exception: {e}")
            return self._fallback_script(topic, content_type, instructions)

    @staticmethod
    def _trim_script(script: str, content_type: str) -> str:
        """Trim script to appropriate length for target duration.

        Target for SHORTS: ~30-45s video (~75-120 words total, 15-25 words/paragraph)
        Target for LONGS:  ~60-90s video (~180-300 words total, 25-40 words/paragraph)
        """
        # Split on double newline to get paragraphs, preserve empty lines
        raw_paragraphs = script.split("\n\n")
        paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
        if not paragraphs:
            return script

        if content_type == "short":
            MAX_PARAGRAPHS = SHORTS_PARAGRAPHS   # 5
            TARGET_WORDS_PER_PARAGRAPH = 22     # 5 × 22 ≈ 110 words → ~35-40s
        else:
            MAX_PARAGRAPHS = LONGS_PARAGRAPHS   # 8
            TARGET_WORDS_PER_PARAGRAPH = 35     # 8 × 35 ≈ 280 words → ~90s

        # Trim to max paragraph count
        paragraphs = paragraphs[:MAX_PARAGRAPHS]

        # Trim each paragraph to target word count at sentence boundary
        trimmed = []
        for para in paragraphs:
            words = para.split()
            if len(words) <= TARGET_WORDS_PER_PARAGRAPH:
                trimmed.append(para)
                continue
            # Find sentence boundary near limit
            idx = min(TARGET_WORDS_PER_PARAGRAPH, len(words))
            # Back up to nearest sentence end
            while idx > 5 and not words[idx - 1].rstrip('.,!?').endswith(('e', 't', 's', 'd')):
                idx -= 1
            # Better: find last punctuation
            last_end = max(
                (i for i, w in enumerate(words) if w.rstrip('.,!?') and w[-1] in '.!?' and i < idx),
                default=idx - 1
            )
            trimmed.append(" ".join(words[:last_end + 1]))

        result = "\n\n".join(trimmed)
        return result

    def _fallback_script(self, topic: str, content_type: str, instructions: str = "") -> dict:
        """Generate a fallback script when LLM is unavailable."""
        paragraphs = [
            f"The topic of '{topic}' is one that most people underestimate.",
            f"Here's what I've learned about '{topic}' that most don't know.",
            f"Let me break this down in a way that actually sticks.",
            f"The truth is, '{topic}' isn't about what you think it is.",
            f"Instead, it's about something much deeper.",
            f"Think about it — how often have you heard advice about '{topic}'?",
            f"Now here's the part nobody tells you about '{topic}'.",
            f"This changes everything you thought you knew.",
            f"If you're serious about understanding '{topic}', this is crucial.",
            f"So what should you do about '{topic}'? Start today.",
        ]

        count = SHORTS_PARAGRAPHS if content_type == "short" else LONGS_PARAGRAPHS
        selected = paragraphs[:min(count, len(paragraphs))]
        script = "\n\n".join(selected)

        print(f"  [Fallback Script] Using template: {len(script)} chars")
        return {"script": script, "sources": ["fallback_template"]}

    def _run_mpt_video(self, script: str, niche: str, content_type: str) -> dict:
        """Run MoneyPrinterTurbo to produce the full video from a script."""
        import uuid
        mpt_uuid = str(uuid.uuid4())
        voice = self._get_voice(niche)
        paragraph_count = SHORTS_PARAGRAPHS if content_type == "short" else LONGS_PARAGRAPHS
        aspect = "9:16" if content_type == "short" else "16:9"

        cmd = [
            sys.executable, str(MPT_CLI),
            "--task-id", mpt_uuid,
            "--video-script", script,
            "--voice-name", voice,
            "--video-language", "en-US",
            "--paragraph-number", str(paragraph_count),
            "--video-aspect", aspect,
            "--video-source", "pexels",
            "--video-transition-mode", "fade-in",
            "--bgm-type", "random",
            "--bgm-volume", "0.15",
            "--subtitle-enabled",
            "--font-size", "55",
            "--font-name", "STHeitiMedium.ttc",
            "--stop-at", "video",
        ]

        print(f"\n  [MPT Video] Starting production...")
        print(f"  [MPT] Voice: {voice} | Aspect: {aspect} | Clips: {paragraph_count}x5s")
        print(f"  [MPT] Transitions: fade-in | BGM: random @ 15%")
        print()

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            timeout_sec = 1200 if content_type == "long" else 900  # 15min for longs, 10min for shorts
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_sec,
                cwd=str(MPT_DIR), env=env,
            )

            if result.returncode != 0:
                print(f"  [MPT] Error: {result.stderr[-500:]}")
                return {"status": "failed", "error": result.stderr[-500:]}

            # Extract JSON from potentially noisy output (ANSI codes, logs, etc.)
            import re
            # Strip ANSI color codes first
            cleaned = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
            # Find last JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}$', cleaned, re.DOTALL)
            if json_match:
                try:
                    output = json.loads(json_match.group())
                except json.JSONDecodeError:
                    output = None
            else:
                output = None

            if output is not None and "task_id" in output:
                return {
                    "status": "success",
                    "task_id": output.get("task_id", mpt_uuid),
                    "result": output.get("result", {}),
                }
            else:
                return {"status": "partial", "raw_output": result.stdout[-1000:]}

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "MPT generation timed out (10min)"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run(self, topic: str, niche: str = "izuku_midoriya", content_type: str = "short") -> dict:
        """Run full hybrid pipeline for one topic."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{niche}_{ts}"

        print(f"\n{'='*60}")
        print(f"  HYBRID RUN: {run_id}")
        print(f"  Topic: {topic}")
        print(f"  Type: {content_type}")
        print(f"{'='*60}\n")

        result = {"run_id": run_id, "topic": topic, "niche": niche, "stages": {}}

        # ── STAGE 1: Script Generation (MPT with RAG context) ────────────────
        print("━" * 40)
        print("  STAGE 1: RAG-enhanced script generation")
        print("━" * 40)

        script_info = self._generate_script_mpt(niche, topic, content_type)
        script = script_info["script"]
        result["stages"]["script"] = {
            "text": script, "chars": len(script), "words": len(script.split()),
            "rag_sources": script_info.get("sources", [])
        }
        print(f"  Script: {len(script)} chars, {len(script.split())} words\n")

        # ── STAGE 2: Director Reviews (skip if LLM unavailable) ────────────
        print("━" * 40)
        print("  STAGE 2: Director review")
        print("━" * 40)

        review = self._safe_director_review(topic, script, niche, content_type)
        result["stages"]["director"] = review

        verdict = review.get("verdict", "APPROVE")
        if verdict == "REJECT":
            print(f"\n  Director REJECTED: {review.get('reasoning', 'No reason')}")
            result["status"] = "rejected"
            self._save_state(result)
            return result

        if verdict == "REVISE":
            revision_notes = review.get("changes_if_revise", "")
            print(f"\n  Director REVISED: {revision_notes[:100]}...")
            script_info = self._generate_script_mpt(
                niche, topic, content_type, instructions=revision_notes
            )
            script = script_info["script"]
            result["stages"]["script"]["text"] = script
            print(f"  Regenerated: {len(script)} chars\n")

        score = review.get("score", "?")
        print(f"  Director approved (score: {score}/10)\n")

        # ── STAGE 3: MPT Video Production ────────────────────────────────────
        print("━" * 40)
        print("  STAGE 3: MoneyPrinterTurbo video production")
        print("━" * 40)

        mpt_result = self._run_mpt_video(script, niche, content_type)
        result["stages"]["mpt_video"] = mpt_result

        if mpt_result.get("status") != "success":
            print(f"\n  MPT failed: {mpt_result.get('error', 'unknown error')}")
            result["status"] = "mpt_failed"
            self._save_state(result)
            return result

        mpt_task_id = mpt_result.get("task_id", "")
        task_dir = MPT_DIR / "storage" / "tasks" / mpt_task_id

        candidates = [
            task_dir / "final-1.mp4",
            task_dir / "combined-1.mp4",
            task_dir / "output" / "output.mp4",
            task_dir / "videos" / "output.mp4",
        ]
        video_path = next((p for p in candidates if p.exists()), None)

        # Copy to our output directory
        output_dir = LONGS_OUTPUT if content_type == "long" else SHORTS_OUTPUT
        output_dir.mkdir(parents=True, exist_ok=True)
        final_video = output_dir / f"{run_id}_mpt.mp4"

        if video_path and video_path.exists():
            shutil.copy2(video_path, final_video)
            duration = self._get_video_duration(final_video)
            result["stages"]["video"] = {
                "video_path": str(final_video),
                "mpt_task_id": mpt_task_id,
                "video_size": final_video.stat().st_size,
                "duration": duration,
            }
            print(f"\n  Video saved: {final_video}")
            print(f"  Size: {final_video.stat().st_size / 1024 / 1024:.1f}MB | Duration: {duration:.1f}s\n")
        else:
            print(f"\n  Video path not found in MPT output")
            result["stages"]["video"] = {"mpt_raw": mpt_result}

        # ── STAGE 3.5: Video Quality Check ──────────────────────────────────
        print("━" * 40)
        print("  STAGE 3.5: Video quality check")
        print("━" * 40)

        quality_passed = False
        if final_video and final_video.exists():
            quality_passed, quality_details = self.video_analyzer.check_or_reject(final_video)
            result["stages"]["quality_check"] = quality_details

            if quality_passed:
                print(f"  ✅ Quality check PASSED (duration: {quality_details['duration']:.1f}s)")
            else:
                print(f"  ❌ Quality check FAILED:")
                for err in quality_details.get("errors", []):
                    print(f"    - {err}")

                # Attempt retry with more paragraphs if duration too short
                if quality_details.get("duration", 0) < 15.0:
                    print(f"\n  Retrying with more paragraphs...")
                    retry_script_info = self._generate_script_mpt(
                        niche, topic, content_type,
                        instructions="Make the script longer, at least 8-10 paragraphs with detailed content."
                    )
                    retry_script = retry_script_info["script"]
                    retry_mpt = self._run_mpt_video(retry_script, niche, content_type)
                    if retry_mpt.get("status") == "success":
                        retry_task_id = retry_mpt.get("task_id", "")
                        retry_task_dir = MPT_DIR / "storage" / "tasks" / retry_task_id
                        retry_candidates = [
                            retry_task_dir / "final-1.mp4",
                            retry_task_dir / "combined-1.mp4",
                            retry_task_dir / "output" / "output.mp4",
                            retry_task_dir / "videos" / "output.mp4",
                        ]
                        retry_video = next((p for p in retry_candidates if p.exists()), None)
                        if retry_video:
                            shutil.copy2(retry_video, final_video)
                            retry_passed, retry_details = self.video_analyzer.check_or_reject(final_video)
                            result["stages"]["quality_check_retry"] = retry_details
                            if retry_passed:
                                quality_passed = True
                                print(f"  ✅ Retry PASSED (duration: {retry_details['duration']:.1f}s)")
                            else:
                                print(f"  ❌ Retry also FAILED")
        else:
            print("  ⚠️  No video to check")

        if not quality_passed:
            print(f"\n  ⚠️  Skipping upload due to quality check failure")
            result["status"] = "quality_failed"
            self._save_state(result)
            return result

        # ── STAGE 4: Publisher + Social Writer (with LLM fallbacks) ─────────
        print("━" * 40)
        print("  STAGE 4: Publisher + Social Writer")
        print("━" * 40)

        upload_meta = self._safe_publisher_prepare(topic, script, niche, content_type)
        result["stages"]["upload_meta"] = upload_meta

        # Try to upload to YouTube if video was produced
        upload_result = {"status": "skipped"}
        if final_video and final_video.exists():
            upload_result = self.publisher.upload_to_youtube(final_video, upload_meta, auto_upload=True)
            result["stages"]["upload"] = upload_result

        caption_path = self.publisher.save_social_captions(upload_meta, {
            "topic": topic,
            "text": script,
        })
        result["stages"]["captions_path"] = str(caption_path)

        posts = self._safe_social_writer(topic, script, niche)
        post_path = self.social_writer.save_posts(posts, {"topic": topic})
        result["stages"]["social_posts"] = str(post_path)

        # ── DONE ─────────────────────────────────────────────────────────────
        result["status"] = "complete"
        result["video_path"] = str(final_video) if video_path and video_path.exists() else ""
        self._save_state(result)

        print(f"\n{'='*60}")
        print(f"  COMPLETE: {run_id}")
        print(f"  Video: {final_video if video_path and video_path.exists() else 'check MPT storage'}")
        print(f"  Captions: {caption_path}")
        print(f"  Posts: {post_path}")
        print(f"{'='*60}\n")

        return result

    @staticmethod
    def _get_video_duration(path: Path) -> float:
        """Get video duration using ffprobe."""
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", str(path)],
                capture_output=True, text=True, timeout=10,
            )
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
        except Exception:
            return 0.0

    def _safe_director_review(self, topic: str, script: str, niche: str, content_type: str) -> dict:
        """Director review with graceful fallback when LLM is unavailable."""
        try:
            return self.director.review({
                "topic": topic,
                "text": script,
                "niche": niche,
                "content_type": content_type,
            })
        except (ConnectionError, TimeoutError, OSError) as e:
            # Network/connectivity issues — lower score but still approve
            print(f"  [Director] LLM connection error ({type(e).__name__}), auto-approving with lower score")
            return {
                "verdict": "APPROVE",
                "score": 5,
                "hook": f"A hook about {topic}",
                "angle": "Practical wisdom with character voice",
                "images": [f"Scene 1: {topic}", f"Scene 2: {topic} context", f"Scene 3: {topic} action"],
                "style": "cinematic, dramatic lighting",
                "title_suggestion": f"Mastering {topic.title()}",
                "tags": [topic.lower(), "motivation", "self-improvement"],
                "reasoning": f"Auto-approved (LLM connection failed). Topic: {topic}",
                "changes_if_revise": "",
            }
        except Exception as e:
            # Other errors (parsing, etc.) — even lower score
            print(f"  [Director] LLM error ({type(e).__name__}: {e}), auto-approving with minimum score")
            return {
                "verdict": "APPROVE",
                "score": 3,
                "hook": f"About {topic}",
                "angle": "Direct and practical",
                "images": [f"Scene 1: {topic}", f"Scene 2: {topic}"],
                "style": "clean, professional",
                "title_suggestion": f"{topic.title()} Explained",
                "tags": [topic.lower(), "motivation"],
                "reasoning": f"Auto-approved (LLM error: {type(e).__name__}). Topic: {topic}",
                "changes_if_revise": "",
            }

    def _safe_publisher_prepare(self, topic: str, script: str, niche: str, content_type: str) -> dict:
        """Publisher metadata with graceful fallback."""
        try:
            return self.publisher.prepare_upload({
                "topic": topic,
                "text": script,
                "niche": niche,
                "content_type": content_type,
            })
        except Exception as e:
            print(f"  [Publisher] LLM unavailable ({type(e).__name__}), using defaults")
            return {
                "youtube": {
                    "title": f"How to Master {topic.title()} | Strategy & Wisdom",
                    "description": f"Deep insights on '{topic}' from a wealthy polymath perspective.\n\n"
                                   f"Topics covered:\n- Key strategies for {topic}\n- Real-world applications\n"
                                   f"- Actionable advice you can use today\n\n"
                                   f"#Motivation #SelfImprovement #Wisdom #{topic.replace(' ', '').lower()}",
                    "tags": [topic.lower(), "motivation", "self improvement", "business", "wisdom", "success"],
                    "category": "Education",
                    "thumbnail_text": [topic.title().split()[0], topic.split()[-1] if len(topic.split()) > 1 else "Wisdom"],
                },
                "social": {
                    "instagram": f"You don't need luck for {topic}. You need strategy. Here's what I've learned after decades of observation...",
                    "twitter": [f"The secret to mastering {topic}? Most people overcomplicate it.",
                                f"Here's the simple truth: {topic} isn't about talent — it's about consistency.",
                                f"Stop making excuses. Start executing. #Motivation"],
                    "tiktok": f"POV: You finally understand {topic} 🧠⚡️ #motivation #wisdom #growth",
                    "linkedin": f"After years of building businesses and studying human nature, here's my take on {topic}.",
                },
                "seo": {
                    "primary_keyword": topic.lower(),
                    "secondary_keywords": [f"{topic} motivation", "self improvement", "wisdom"],
                    "best_time": "6-9 AM or 7-10 PM local time",
                },
            }

    def _safe_social_writer(self, topic: str, script: str, niche: str) -> dict:
        """Social media posts with graceful fallback."""
        try:
            return self.social_writer.write_posts({
                "topic": topic,
                "text": script,
                "niche": niche,
            })
        except Exception as e:
            print(f"  [SocialWriter] LLM unavailable ({type(e).__name__}), using template")
            topic_words = topic.split()
            return {
                "instagram": f"{topic_words[0].capitalize()} changes everything when you understand it deeply. Here's my take after years of experience.\n\n#Motivation #Wisdom #GrowthMindset",
                "twitter": [f"The hardest truth about {topic}? Most people never figure it out.",
                            f"But once you do — everything shifts. Here's what I know.",
                            f"Don't wait for permission. Start building your {topic} skills today."],
                "tiktok": f"If you want to master {topic}, this is your sign. 🎯",
                "linkedin": f"Here's something I've learned about {topic} that most people miss: consistency beats intensity every time.",
                "one_liner": f"Mastery of {topic} isn't about talent — it's about showing up when others quit.",
            }

    def batch(self, topics_file: str, niche: str = "izuku_midoriya"):
        """Run hybrid pipeline for multiple topics."""
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

        complete = sum(1 for r in results if r["status"] == "complete")
        failed = sum(1 for r in results if r["status"] in ("rejected", "mpt_failed"))

        print(f"\n{'='*60}")
        print(f"  BATCH COMPLETE: {len(results)} videos")
        print(f"  Successful: {complete}")
        print(f"  Failed/Rejected: {failed}")
        print(f"{'='*60}")

    def status(self) -> dict:
        """Show pipeline status."""
        state_files = list(self.state_dir.glob("*.json"))
        complete = sum(
            1 for f in state_files
            if json.loads(f.read_text()).get("status") == "complete"
        )
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
    parser = argparse.ArgumentParser(description="Socio Business Hybrid Orchestrator")
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
    orch = HybridOrchestrator()

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
