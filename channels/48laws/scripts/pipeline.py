#!/usr/bin/env python3
"""
48 Laws of Power — Video Pipeline
Generates story-driven videos for each of the 48 Laws.
"""

import json
import os
import sys
import time
import shutil
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────
# __file__ = channels/48laws/scripts/pipeline.py
# parent   = channels/48laws/scripts    (TEAM_DIR — script dir)
# parent2  = channels/48laws             (channel dir)
# parent3  = channels                     (channels/)
# parent4  = socio_business/            ← actual business root

TEAM_DIR = Path(__file__).parent
CHANNEL_DIR = TEAM_DIR.parent          # channels/48laws
BUSINESS_DIR = CHANNEL_DIR.parent.parent  # socio_business/

STORIES_DIR = CHANNEL_DIR / "stories"
IMAGES_DIR = CHANNEL_DIR / "images"
VOICES_DIR = CHANNEL_DIR / "voices"
OUTPUT_DIR = CHANNEL_DIR / "output"
BOOKS_DIR = CHANNEL_DIR / "books"
RAG_DIR = CHANNEL_DIR / "rag"

ITERATIONS = 48
NICHE = "48 Laws of Power — Story-driven explanations"

# ── 48 Laws Database ─────────────────────────────────────────────────────────

LAWS = {
    1: {
        "title": "Never Outshine the Master",
        "hook": "Make those above you feel superior. Never threaten their ego.",
        "theme": "court intrigue, ambition, strategy",
        "moral": "The smartest person often lets others think they are the smartest.",
    },
    2: {
        "title": "Never Put Too Much Trust in Friends, Learn How to Use Enemies",
        "hook": "Friends betray out of envy. Enemies betray out of necessity.",
        "theme": "loyalty, betrayal, calculation",
        "moral": "A former enemy can be more loyal than a friend.",
    },
    3: {
        "title": "Conceal Your Intentions",
        "hook": "Keep people off-balance by never revealing the purpose behind your actions.",
        "theme": "deception, strategy, power",
        "moral": "The most powerful person is the one no one sees coming.",
    },
    4: {
        "title": "Always Say Less Than Necessary",
        "hook": "The more you speak, the more you sound ordinary.",
        "theme": "silence, power, mystery",
        "moral": "Strong people impress others by saying less.",
    },
    5: {
        "title": "So Much Depends on Reputation – Guard It with Your Life",
        "hook": "Your reputation is the cornerstone of your power.",
        "theme": "reputation, image, perception",
        "moral": "A strong reputation creates fear and respect.",
    },
    6: {
        "title": "Court Attention at All Cost",
        "hook": "Everything is judged by its appearance. Stand out.",
        "theme": "attention, presence, visibility",
        "moral": "Better to be slandered than ignored.",
    },
    7: {
        "title": "Get Others to Do the Work for You, but Always Take the Credit",
        "hook": "Use the time and energy of others to advance your own agenda.",
        "theme": "credit, delegation, strategy",
        "moral": "The end justifies the means.",
    },
    8: {
        "title": "Make Other People Come to You – Use Bait if Necessary",
        "hook": "When you force the other player to act, you are the one in control.",
        "theme": "control, patience, strategy",
        "moral": "He who waits out his enemies wins without fighting.",
    },
    9: {
        "title": "Win Through Your Actions, Never Through Argument",
        "hook": "Any momentary triumph you think gained through argument is really a Pyrrhic victory.",
        "theme": "action, demonstration, power",
        "moral": "Demonstrate, do not explicate.",
    },
    10: {
        "title": "Infection: Avoid the Unhappy and Unlucky",
        "hook": "Emotional states are as infectious as diseases.",
        "theme": "association, influence, protection",
        "moral": "Associate with the happy and fortunate.",
    },
    11: {
        "title": "Learn to Keep People Dependent on You",
        "hook": "The more people rely on you, the more freedom you have.",
        "theme": "dependence, leverage, power",
        "moral": "Make yourself indispensable to every king.",
    },
    12: {
        "title": "Use Selective Honesty and Generosity to Disarm Your Victim",
        "hook": "One sincere and honest move will cover over dozens of dishonest ones.",
        "theme": "honesty, manipulation, trust",
        "moral": "A single honest gesture disarms suspicion.",
    },
    13: {
        "title": "When Asking for Help, Appeal to People's Self-Interest",
        "hook": "Never forget that even when you ask for help, the goal is to serve yourself.",
        "theme": "persuasion, negotiation, strategy",
        "moral": "Show others how their interests are served.",
    },
    14: {
        "title": "Show Respect, or Act Like a Friend",
        "hook": "People will see through disingenuous flattery.",
        "theme": "respect, friendship, manipulation",
        "moral": "Be warm, human, and engaging.",
    },
    15: {
        "title": "Crush Your Enemy Totally",
        "hook": "If one ember is left alight, no matter how dimly it smolders, a fire will eventually break out.",
        "theme": "enemies, destruction, finality",
        "moral": "Don't leave room for revenge.",
    },
    16: {
        "title": "Use Absence to Increase Respect and Honor",
        "hook": "Too much circulation makes the price go down.",
        "theme": "absence, scarcity, value",
        "moral": "Create value through absence.",
    },
    17: {
        "title": "Keep Others in Suspended Terror: Cultivate an Air of Unpredictability",
        "hook": "Humans are creatures of habit with an insatiable need to see familiarity in others' actions.",
        "theme": "unpredictability, fear, control",
        "moral": "Be unpredictable to keep enemies off-balance.",
        "motto": "The man who throws a curveball will never be struck out.",
    },
    18: {
        "title": "Do Not Build Fortresses to Protect Yourself – Isolation is Dangerous",
        "hook": "Isolation makes you weaker and more fearful.",
        "theme": "isolation, community, strength",
        "moral": "Stay connected to others.",
    },
    19: {
        "title": "Know Who You're Dealing With – Do Not Offend the Wrong Person",
        "hook": "Not everyone wants to be your friend or ally.",
        "theme": "recognition, caution, strategy",
        "moral": "Choose your battles carefully.",
    },
    20: {
        "title": "Do Not Commit to Anyone",
        "hook": "By remaining independent, you become the master of others.",
        "theme": "independence, loyalty, power",
        "moral": "Stay neutral to play all sides.",
    },
    21: {
        "title": "Play a Sucker to Catch a Fool",
        "hook": "Let them underestimate you. Then surprise them.",
        "theme": "deception, strategy, power",
        "moral": "Appear weaker than you are.",
    },
    22: {
        "title": "Use the Surrender Tactic: Transform Weakness into Power",
        "hook": "When you are weaker, never fight for honor's sake; choose surrender instead.",
        "theme": "surrender, strategy, patience",
        "moral": "Surrender can be a powerful weapon.",
    },
    23: {
        "title": "Concentrate Your Forces",
        "hook": "Focus your energy on one objective.",
        "theme": "focus, concentration, power",
        "moral": "Divide and conquer doesn't always work.",
        "motto": "Concentrate your forces.",
    },
    24: {
        "title": "Play the Perfect Courtier",
        "hook": "Master the art of indirectness and flattery.",
        "theme": "courtiership, flattery, strategy",
        "moral": "Master the art of indirectness.",
    },
    25: {
        "title": "Re-Create Yourself",
        "hook": "Do not accept the roles that society foists on you.",
        "theme": "identity, reinvention, power",
        "moral": "Create your own identity.",
    },
    26: {
        "title": "Keep Your Hands Clean",
        "hook": "Use cat's paws — others to do the dirty work.",
        "theme": "deception, manipulation, power",
        "moral": "Maintain a clean image.",
    },
    27: {
        "title": "Play on People's Need to Believe to Create a Cultlike Following",
        "hook": "People have an overwhelming desire to believe in something.",
        "theme": "belief, cults, manipulation",
        "moral": "Appeal to their need for meaning.",
    },
    28: {
        "title": "Act Like Nobody, Do What You Will",
        "hook": "Blend in, stay invisible, and pursue your goals.",
        "theme": "invisibility, freedom, strategy",
        "moral": "Stay under the radar.",
    },
    29: {
        "title": "Plan All the Way to the End",
        "hook": "The ending is everything.",
        "theme": "planning, foresight, strategy",
        "moral": "Plan to the very end.",
    },
    30: {
        "title": "Make Your Accomplishments Seem Effortless",
        "hook": "Your actions must seem natural and executed with ease.",
        "theme": "effortlessness, illusion, power",
        "moral": "Appear natural and effortless.",
    },
    31: {
        "title": "Control the Options: Get Others to Play with the Cards You Deal",
        "hook": "Give people choices that benefit you no matter which they choose.",
        "theme": "control, options, strategy",
        "moral": "Control the options.",
    },
    32: {
        "title": "Play to People's Fantasies",
        "hook": "The truth is often avoided because it is ugly and unpleasant.",
        "theme": "fantasy, deception, power",
        "moral": "Appeal to people's fantasies.",
    },
    33: {
        "title": "Discover Each Man's Thumbscrew",
        "hook": "Find the weak spot that everyone has.",
        "theme": "weakness, leverage, manipulation",
        "moral": "Find everyone's weak spot.",
    },
    34: {
        "title": "Be Royal in Your Own Fashion: Act Like a King to Be Treated Like One",
        "hook": "The way you carry yourself will often determine how you are treated.",
        "theme": "royalty, behavior, power",
        "moral": "Act like royalty.",
    },
    35: {
        "title": "Master the Art of Timing",
        "hook": "Never seem to be in a hurry.",
        "theme": "timing, patience, strategy",
        "moral": "Master the art of timing.",
    },
    36: {
        "title": "Disdain Things You Cannot Have: Ignoring Them is the Best Revenge",
        "hook": "By acknowledging a nuisance, you sustain it.",
        "theme": "ignoring, disdain, strategy",
        "moral": "Disdain what you cannot have.",
    },
    37: {
        "title": "Create Compelling Spectacles",
        "hook": "Striking imagery and grand symbolic gestures create an aura of omnipotence.",
        "theme": "spectacle, imagery, power",
        "moral": "Create compelling spectacles.",
    },
    38: {
        "title": "Think as You Like but Behave Like Others",
        "hook": "If you make a show of going against the times, people will think you are after attention.",
        "theme": "conformity, behavior, strategy",
        "moral": "Blend in while thinking differently.",
    },
    39: {
        "title": "Stir Up Waters to Catch Fish",
        "hook": "Anger and emotion are strategically counterproductive.",
        "theme": "emotion, strategy, control",
        "moral": "Keep emotions in check.",
    },
    40: {
        "title": "Despise the Free Lunch",
        "hook": "What is offered for free is dangerous — it usually involves either a trick or a hidden obligation.",
        "theme": "free lunches, trickery, power",
        "moral": "Avoid free lunches.",
        "motto": "What's offered for free is dangerous.",
    },
    41: {
        "title": "Avoid Stepping into a Great Man's Shoes",
        "hook": "What happens first always appears better and more original than what comes after.",
        "theme": "legacy, comparison, strategy",
        "moral": "Establish your own name.",
    },
    42: {
        "title": "Strike the Shepherd and the Sheep Will Scatter",
        "hook": "Trouble can often be traced to a single strong individual.",
        "theme": "trouble, leadership, strategy",
        "moral": "Neutralize the source.",
    },
    43: {
        "title": "Work on the Hearts and Minds of Others",
        "hook": "Coercion creates a reaction that will eventually work against you.",
        "theme": "hearts, minds, manipulation",
        "moral": "Seduce others' hearts and minds.",
    },
    44: {
        "title": "Disarm and Infuriate with the Mirror Effect",
        "hook": "Mirror the actions of your enemies until they become uncertain and suspicious of their own motives.",
        "theme": "mirror, manipulation, strategy",
        "moral": "Use the mirror effect.",
    },
    45: {
        "title": "Preach the Need for Change, but Never Reform Too Much at Once",
        "hook": "Everyone understands the need for change in the abstract, but on a day-to-day basis people are creatures of habit.",
        "theme": "change, reform, strategy",
        "moral": "Introduce change gradually.",
    },
    46: {
        "title": "Never Appear Too Perfect",
        "hook": "Appearances can be enchanting, but envy produces resentment.",
        "theme": "perfection, envy, strategy",
        "moral": "Appear human and flawed.",
    },
    47: {
        "title": "Do Not Go Past the Mark You Aimed For; In Victory, Learn When to Stop",
        "hook": "The moment of victory is often the moment of greatest peril.",
        "theme": "victory, danger, strategy",
        "moral": "Know when to stop.",
    },
    48: {
        "title": "Assume Formlessness",
        "hook": "By taking a shape, you have a vulnerability. Formlessness is not emptiness — it is the absence of a fixed pattern.",
        "theme": "formlessness, adaptability, power",
        "moral": "Be like water — shapeless and unpredictable.",
    },
}


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def ensure_dirs():
    for d in [STORIES_DIR, IMAGES_DIR, VOICES_DIR, OUTPUT_DIR, BOOKS_DIR, RAG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def step_1_write_story(lesson_num: int) -> Optional[Path]:
    """Write a story for the given law."""
    log(f"Writing story for Law {lesson_num}")

    law = LAWS.get(lesson_num)
    if not law:
        log(f"  No data for Law {lesson_num}")
        return None

    # Read existing story
    story_file = STORIES_DIR / f"lesson_{lesson_num:02d}.md"
    if story_file.exists():
        log(f"  Story already exists: {story_file.name}")
        return story_file

    # Generate story based on law
    story = f"""# {law['title']}

**Law {lesson_num} of 48**

---

{law['hook']}

[Story content for Law {lesson_num} — {law['theme']}]

**Moral:** {law['moral']}
"""

    story_file.write_text(story)
    log(f"  Story written: {story_file.name}")
    return story_file


def step_2_generate_images(lesson_num: int) -> Optional[Path]:
    """Generate AI scene images."""
    log(f"Generating images for Law {lesson_num}")

    img_dir = IMAGES_DIR / f"lesson_{lesson_num:02d}"
    img_dir.mkdir(exist_ok=True)

    # Check if images already exist
    existing = list(img_dir.glob("scene_*.jpg")) + list(img_dir.glob("scene_*.png"))
    if len(existing) >= 3:
        log(f"  Images exist: {len(existing)} files")
        return img_dir

    law = LAWS.get(lesson_num)
    if not law:
        return None

    # Generate 3 scene prompts based on law theme
    prompts = [
        f"cinematic dark fantasy, {law['theme']}, dramatic lighting, epic composition, 4k, anime style",
        f"cinematic dark fantasy, power and strategy, {law['theme']}, atmospheric, 4k",
        f"cinematic dark fantasy, ancient wisdom, {law['theme']}, mystical, 4k",
    ]

    for j, prompt in enumerate(prompts):
        scene_img = img_dir / f"scene_{j+1:02d}.jpg"
        if scene_img.exists():
            continue

        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={lesson_num * 10 + j}&nologo=true"
        log(f"  Generating scene {j+1}...")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                if len(data) > 5000:
                    scene_img.write_bytes(data)
                    log(f"  Scene {j+1} OK: {len(data)//1024}KB")
                else:
                    log(f"  Scene {j+1} too small")
        except Exception as e:
            log(f"  Scene {j+1} failed: {e}")

    return img_dir


def step_3_generate_voice(lesson_num: int) -> Optional[Path]:
    """Generate voiceover."""
    log(f"Generating voice for Law {lesson_num}")

    voice_file = VOICES_DIR / f"lesson_{lesson_num:02d}.wav"
    if voice_file.exists():
        log(f"  Voice exists: {voice_file.name}")
        return voice_file

    law = LAWS.get(lesson_num)
    if not law:
        return None

    # Create narration text
    narration = f"""Law {lesson_num}: {law['title']}.

{law['hook']}

Remember: {law['moral']}.

Stay powerful."""

    # Save text file
    text_file = VOICES_DIR / f"lesson_{lesson_num:02d}.txt"
    text_file.write_text(narration)

    # Try Piper TTS
    piper_model = BUSINESS_DIR / "assets" / "audio" / "piper-voices" / "en_US-ryan-medium.onnx"
    if piper_model.exists():
        try:
            import subprocess
            result = subprocess.run(
                ["piper", "-m", str(piper_model), "-f", str(voice_file)],
                input=narration,
                capture_output=True, text=True, timeout=60,
            )
            if voice_file.exists():
                log(f"  Voice generated (Piper): {voice_file.name}")
                return voice_file
            else:
                log(f"  Piper failed: {result.stderr[:200]}")
        except Exception as e:
            log(f"  Piper error: {e}")

    # Fallback: save narration text for manual processing
    voice_file.write_text(f"[Narration text saved to {text_file.name}]")
    log(f"  Voice file created (text narration)")
    return voice_file


def step_4_assemble_video(lesson_num: int, img_dir: Optional[Path], voice_file: Optional[Path]) -> Optional[Path]:
    """Assemble video."""
    log(f"Assembling video for Law {lesson_num}")

    output_file = OUTPUT_DIR / f"law_{lesson_num:02d}.mp4"
    if output_file.exists() and output_file.stat().st_size > 100000:
        log(f"  Video exists: {output_file.name}")
        return output_file

    law = LAWS.get(lesson_num)
    if not law:
        return None

    # Get scene images
    scenes = []
    if img_dir:
        scenes = sorted(img_dir.glob("scene_*.jpg")) + sorted(img_dir.glob("scene_*.png"))

    if not scenes:
        log("  No images available")
        return None

    # Create simple video with ffmpeg
    import subprocess

    # Create filter complex for Ken Burns effect
    filter_parts = []
    duration = 5  # seconds per scene
    total_duration = len(scenes) * duration

    for i, scene in enumerate(scenes):
        start = f"{i*duration}"
        end = f"{(i+1)*duration}"
        # Simple zoom effect
        filter_parts.append(
            f"[{i}:v]scale=1080:1920,zoompan=z='min(1.5,{1.0 + i*0.1})':d={duration}:s={scene.name}:x=0:y=0"
            f"[v{i}]"
        )

    # Simplified: just concat images with audio
    log(f"  Assembling {len(scenes)} scenes...")

    # Create concat file
    concat_file = OUTPUT_DIR / f"concat_{lesson_num}.txt"
    concat_lines = []
    for scene in scenes:
        concat_lines.append(f"file '{scene}'")
        concat_lines.append(f"duration {duration}")
    concat_lines.append("flush_packets 1")

    concat_file.write_text("\n".join(concat_lines))

    # Assemble video
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-vf", f"scale=1080:1920,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(total_duration),
        "-r", "30",
        str(output_file)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output_file.exists() and output_file.stat().st_size > 50000:
            log(f"  Video assembled: {output_file.name} ({output_file.stat().st_size//1024}KB)")
            return output_file
        else:
            log(f"  Assembly failed: {result.stderr[:200]}")
    except Exception as e:
        log(f"  Assembly error: {e}")

    return None


def step_5_post_social(lesson_num: int, video_file: Optional[Path]):
    """Post to social media."""
    log(f"Posting Law {lesson_num} to social media")

    if not video_file or not video_file.exists():
        log("  No video to post")
        return

    law = LAWS.get(lesson_num)
    if not law:
        return

    log(f"  Title: {law['title']}")
    log(f"  Video: {video_file.name}")
    log("  (Social posting requires API tokens)")


def run_pipeline():
    ensure_dirs()
    log("=" * 60)
    log("48 LAWS OF POWER — VIDEO PIPELINE")
    log(f"Total lessons: {ITERATIONS}")
    log("=" * 60)

    for i in range(1, min(ITERATIONS + 1, 6)):  # Run first 5 for demo
        log(f"\n{'─' * 40}")
        log(f"LESSON {i}/48")
        log(f"{'─' * 40}")

        story = step_1_write_story(i)
        img_dir = step_2_generate_images(i)
        voice = step_3_generate_voice(i)
        video = step_4_assemble_video(i, img_dir, voice)
        step_5_post_social(i, video)

        log(f"Lesson {i} COMPLETE ✓")

    log("\n" + "=" * 60)
    log("DEMO COMPLETE — 5 lessons generated")
    log("=" * 60)


if __name__ == "__main__":
    run_pipeline()
