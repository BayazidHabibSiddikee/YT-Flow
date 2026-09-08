#!/usr/bin/env python3
"""
YT-Flow: Written Post Generator
=================================
Generates written posts explaining how the pipeline works.
Posts are written in Izuku Midoriya's voice.

Usage:
    python3 scripts/generate_post.py --topic face-swap
    python3 scripts/generate_post.py --topic body-swap
    python3 scripts/generate_post.py --topic video-automation
    python3 scripts/generate_post.py --topic release-scheduler
    python3 scripts/generate_post.py --topic full-pipeline
    python3 scripts/generate_post.py --topic all
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_DIR, "posts")
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Post templates in Izuku Midoriya's voice
POSTS = {
    "face-swap": {
        "title": "How Face Swapping Actually Works",
        "content": """🧠 How Face Swapping Actually Works

I built a face-swap pipeline using AI. Here's exactly how it works:

1️⃣ Face Detection
First, the AI finds every face in both images using a model called buffalo_l. It maps 68 key points on each face — eyes, nose, jawline, everything.

2️⃣ Face Alignment
The source face is rotated, scaled, and warped to match the target face's angle and position. Even if one person is looking left and the other right, the AI adjusts.

3️⃣ Feature Extraction
A neural network called inswapper_128 analyzes the source face — skin tone, lighting, expression, even the way light hits the cheekbones. It creates a "face embedding" — a mathematical representation of everything that makes that face unique.

4️⃣ Face Generation
The AI replaces the target face with the source face while preserving the target's original lighting, background, and body. It's not a copy-paste — it's a full regeneration.

5️⃣ Blending
The edges are smoothed, colors are matched, and the final result is composited. If done right, you can't tell it was swapped.

🔧 My Setup:
- Model: inswapper_128.onnx (529MB)
- Detection: buffalo_l (326MB)
- Runtime: CPU (GPU is faster but not required)
- Time per image: ~5-15 seconds

The models are free. The code is open source. The only cost is compute.

I'm sharing this because understanding the tech demystifies it. AI isn't magic — it's math. And once you understand the math, you can build anything.

What do you want me to break down next?

#faceswap #AI #machinelearning #tech #buildinpublic""",
        "platforms": ["twitter", "facebook", "instagram", "youtube_community"],
        "hashtags": ["#faceswap", "#AI", "#machinelearning", "#tech", "#buildinpublic"]
    },

    "body-swap": {
        "title": "How Body Swapping Works (Full Pipeline)",
        "content": """🏃 How Body Swapping Works — Full Pipeline

Face swapping is common now. Body swapping is the next level. Here's how I built it:

1️⃣ Pose Detection
MediaPipe Pose detects 33 body keypoints — shoulders, elbows, wrists, hips, knees, ankles. It creates a "stick figure" skeleton of the person in the target video.

2️⃣ Body Segmentation
The AI isolates the body from the background using skin color detection and contour analysis. It creates a mask — white where the body is, black everywhere else.

3️⃣ Body Warping
Using affine transformation, the source body is stretched, rotated, and aligned to match the target's pose. If the target is raising their right arm, the source's right arm is raised to match.

4️⃣ Texture Transfer
The source person's appearance — skin, clothing, muscle definition — is transferred onto the warped body shape.

5️⃣ Blending
The warped source is composited onto the target background. Colors are matched, edges are smoothed, and shadows are added for realism.

🔧 My Setup:
- Pose: MediaPipe Pose (auto-downloaded)
- Segmentation: HSV skin detection + contour analysis
- Warping: Affine transform (3-point alignment)
- Blending: Alpha compositing with mask

⚠️ Limitations:
- Works best on static images or short clips
- Source and target should have similar body types
- GPU recommended for video (CPU works for images)

Body swap is much heavier than face swap. But the results are worth it.

Next: How I automate the entire video pipeline.

#bodyswap #AI #mediapipe #computervision #buildinpublic""",
        "platforms": ["twitter", "facebook", "instagram", "youtube_community"],
        "hashtags": ["#bodyswap", "#AI", "#mediapipe", "#computervision", "#buildinpublic"]
    },

    "video-automation": {
        "title": "How I Automated My Entire Video Pipeline",
        "content": """🎬 How I Automated My Entire Video Pipeline

I went from 10 hours of manual editing to fully automated video production. Here's the system:

📹 Step 1: Video Generation
- AI generates short clips (5-10 seconds) from text prompts
- Tools: HuggingFace models, custom pipelines
- Output: Raw footage ready for editing

✂️ Step 2: Video Processing
- FFmpeg extends clips to 22+ seconds (YouTube minimum)
- Loops footage smoothly with stream copy (no quality loss)
- Adds styled subtitles burned into the video
- Font: Arial Black, 32px, white with black outline

📝 Step 3: Subtitle Generation
- Whisper AI transcribes any speech
- Subtitles are styled and burned in (not optional overlay)
- Timing is auto-synced to speech patterns

🎨 Step 4: Post-Processing
- Color correction, edge smoothing
- Thumbnail generation
- Metadata tagging

⏱️ Time Saved:
- Manual: 2-3 hours per video
- Automated: 5 minutes per video
- 90% reduction in production time

The key insight: automate the repetitive, keep the creative.

I still choose the topics, write the hooks, and approve the final cut. AI handles the grind.

#videoautomation #ffmpeg #AI #contentcreator #buildinpublic""",
        "platforms": ["twitter", "facebook", "instagram", "youtube_community"],
        "hashtags": ["#videoautomation", "#ffmpeg", "#AI", "#contentcreator", "#buildinpublic"]
    },

    "release-scheduler": {
        "title": "How I Schedule Videos Across Platforms Automatically",
        "content": """📅 How I Schedule Videos Across Platforms Automatically

Posting consistently is the hardest part of content creation. So I built a scheduler.

🗂️ The Queue System:
Every video goes into a release queue with:
- Video file path
- Target platform (YouTube, TikTok, Instagram, Facebook)
- Scheduled date and time
- Title, description, hashtags
- Status: scheduled → released

⏰ The Automation:
- Systemd timers check the queue every hour
- When a video's time comes, it's automatically published
- Every action is logged with timestamps
- Failed releases are retried

📊 The Tracking:
- Pipeline log tracks every operation
- Release queue tracks every video
- Cron execution log tracks every automation run
- Posts log tracks every social media post

🔧 The Stack:
- Python for logic
- Systemd timers for scheduling (not cron — more reliable)
- JSON files for queue storage (simple, human-readable)
- FFmpeg for video processing

📈 Current Queue:
- 3 videos ready for release
- Platforms: YouTube, TikTok, Instagram
- Schedule: TBD (setting up optimal posting times)

The goal: upload once, publish everywhere, on time, every time.

#automation #contentcreator #socialmedia #scheduling #buildinpublic""",
        "platforms": ["twitter", "facebook", "instagram", "youtube_community"],
        "hashtags": ["#automation", "#contentcreator", "#socialmedia", "#scheduling", "#buildinpublic"]
    },

    "full-pipeline": {
        "title": "The Full Pipeline: From Idea to Published Video",
        "content": """🚀 The Full Pipeline: From Idea to Published Video

Here's the entire system — start to finish:

1️⃣ IDEA
I choose a topic based on audience demand. Gym motivation, business wisdom, anime crossovers.

2️⃣ GENERATION
AI generates short video clips. Sometimes I use existing footage. Sometimes I create from scratch.

3️⃣ EDITING
- FFmpeg extends to 22+ seconds
- Subtitles are generated and burned in
- Styled with Arial Black, white on black outline
- No generic CTAs — only business/gym/motivation text

4️⃣ FACE/BODY SWAP (Optional)
- Face swap: inswapper_128.onnx + buffalo_l
- Body swap: MediaPipe Pose + affine warping
- Combined: face first, then body

5️⃣ QUEUE
Every finished video enters the release queue with platform, time, title, description.

6️⃣ SCHEDULE
Systemd timers check the queue hourly. When it's time, the video is published.

7️⃣ PUBLISH
Posted to YouTube, TikTok, Instagram, Facebook — simultaneously or staggered.

8️⃣ TRACK
Every action is logged. Every post is tracked. Every video's performance is recorded.

📊 The Numbers:
- 3 videos in queue
- 4 platforms targeted
- 8 pipeline steps
- 1 human (me) overseeing it all

This is how you scale content creation without burning out.

#buildinpublic #contentcreator #AI #automation #pipeline""",
        "platforms": ["twitter", "facebook", "instagram", "youtube_community"],
        "hashtags": ["#buildinpublic", "#contentcreator", "#AI", "#automation", "#pipeline"]
    }
}


def generate_post(topic):
    """Generate a post for the given topic."""
    if topic not in POSTS:
        print(f"❌ Unknown topic: {topic}")
        print(f"Available: {', '.join(POSTS.keys())}")
        return None

    post = POSTS[topic]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{topic}_{timestamp}.json"
    filepath = os.path.join(POSTS_DIR, filename)

    post_data = {
        "id": f"POST-{timestamp}",
        "topic": topic,
        "title": post["title"],
        "content": post["content"],
        "platforms": post["platforms"],
        "hashtags": post["hashtags"],
        "status": "generated",
        "created_at": datetime.now().isoformat(),
        "filename": filename,
    }

    with open(filepath, "w") as f:
        json.dump(post_data, f, indent=2)

    print(f"✅ Post generated: {filename}")
    print(f"   Topic: {topic}")
    print(f"   Platforms: {', '.join(post['platforms'])}")
    print(f"   Length: {len(post['content'])} chars")
    return post_data


def list_posts():
    """List all generated posts."""
    posts = [f for f in os.listdir(POSTS_DIR) if f.endswith(".json")]
    if not posts:
        print("No posts generated yet.")
        return

    print(f"\n📝 Generated Posts ({len(posts)}):")
    print("-" * 60)
    for filename in sorted(posts):
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath) as f:
            data = json.load(f)
        status_icon = "✅" if data["status"] == "published" else "⏳"
        print(f"  {status_icon} {data['id']} | {data['topic']:20} | {data['status']}")
    print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YT-Flow Post Generator")
    parser.add_argument("--topic", help="Post topic (or 'all')")
    parser.add_argument("--list", action="store_true", help="List all posts")
    args = parser.parse_args()

    if args.list:
        list_posts()
    elif args.topic == "all":
        for topic in POSTS:
            generate_post(topic)
        print(f"\n✅ All {len(POSTS)} posts generated")
    elif args.topic:
        generate_post(args.topic)
    else:
        print("Usage:")
        print("  python3 generate_post.py --topic face-swap")
        print("  python3 generate_post.py --topic body-swap")
        print("  python3 generate_post.py --topic video-automation")
        print("  python3 generate_post.py --topic release-scheduler")
        print("  python3 generate_post.py --topic full-pipeline")
        print("  python3 generate_post.py --topic all")
        print("  python3 generate_post.py --list")
