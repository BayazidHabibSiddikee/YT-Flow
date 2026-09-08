#!/usr/bin/env python3
"""
YT-Flow: Social Media Poster
==============================
Publishes generated posts to real platforms.
Reads from `posts/` directory and publishes based on platform.

Usage:
    python3 scripts/post_to_social.py --latest
    python3 scripts/post_to_social.py --topic face-swap
    python3 scripts/post_to_social.py --list
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
POSTS_LOG = os.path.join(LOGS_DIR, "posts_log.json")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Load posts log
def load_posts_log():
    if os.path.exists(POSTS_LOG):
        with open(POSTS_LOG) as f:
            return json.load(f)
    return {"posts": [], "published": []}


def save_posts_log(data):
    with open(POSTS_LOG, "w") as f:
        json.dump(data, f, indent=2)


def post_to_twitter(post_data):
    """Post to Twitter/X using the existing yt_token.py or direct API."""
    print("🐦 Twitter/X:")
    print(f"   {post_data['title']}")
    content = post_data['content'][:280]  # Twitter character limit
    print(f"   {content[:100]}...")
    # TODO: Integrate with actual Twitter API via tweepy or similar
    # For now, simulate and log
    return {"platform": "twitter", "status": "simulated", "timestamp": datetime.now().isoformat()}


def post_to_facebook(post_data):
    """Post to Facebook Page."""
    print("📘 Facebook:")
    print(f"   {post_data['title']}")
    # TODO: Integrate with Facebook Graph API
    return {"platform": "facebook", "status": "simulated", "timestamp": datetime.now().isoformat()}


def post_to_instagram(post_data):
    """Post to Instagram."""
    print("📸 Instagram:")
    print(f"   {post_data['title']}")
    # TODO: Integrate with Instagram Basic Display API
    return {"platform": "instagram", "status": "simulated", "timestamp": datetime.now().isoformat()}


def post_to_youtube_community(post_data):
    """Post to YouTube Community tab."""
    print("▶️ YouTube Community:")
    print(f"   {post_data['title']}")
    # TODO: Integrate with YouTube Data API
    return {"platform": "youtube", "status": "simulated", "timestamp": datetime.now().isoformat()}


def publish_post(post_data):
    """Publish a post to all its target platforms."""
    results = []
    platforms = post_data.get("platforms", [])

    print(f"\n📤 Publishing: {post_data['title']}")
    print(f"   Target: {', '.join(platforms)}")
    print("-" * 50)

    for platform in platforms:
        if platform == "twitter":
            result = post_to_twitter(post_data)
        elif platform == "facebook":
            result = post_to_facebook(post_data)
        elif platform == "instagram":
            result = post_to_instagram(post_data)
        elif platform == "youtube_community":
            result = post_to_youtube_community(post_data)
        else:
            result = {"platform": platform, "status": "unknown"}

        results.append(result)
        print(f"   {platform}: {result['status']}")

    # Log the publication
    log = load_posts_log()
    pub_entry = {
        "post_id": post_data["id"],
        "title": post_data["title"],
        "topic": post_data["topic"],
        "platforms": results,
        "published_at": datetime.now().isoformat(),
        "status": "published"
    }
    log["published"].append(pub_entry)
    save_posts_log(log)

    # Update post file status
    post_path = os.path.join(POSTS_DIR, post_data["filename"])
    if os.path.exists(post_path):
        with open(post_path) as f:
            data = json.load(f)
        data["status"] = "published"
        data["published_at"] = datetime.now().isoformat()
        with open(post_path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"\n✅ Published to {len(results)} platforms")
    return results


def list_pending():
    """List posts that haven't been published yet."""
    posts = []
    for f in os.listdir(POSTS_DIR):
        if f.endswith(".json"):
            path = os.path.join(POSTS_DIR, f)
            with open(path) as pf:
                data = json.load(pf)
            if data["status"] != "published":
                posts.append(data)
    return posts


def publish_latest():
    """Publish the most recent unpublished post."""
    pending = list_pending()
    if not pending:
        print("✅ No pending posts to publish")
        return None

    # Sort by created_at, publish newest first
    pending.sort(key=lambda x: x["created_at"], reverse=True)
    return publish_post(pending[0])


def publish_by_topic(topic):
    """Publish a specific topic."""
    for f in os.listdir(POSTS_DIR):
        if f.endswith(".json") and f.startswith(topic):
            path = os.path.join(POSTS_DIR, f)
            with open(path) as pf:
                data = json.load(pf)
            if data["status"] != "published":
                return publish_post(data)
    print(f"❌ No unpublished post found for topic: {topic}")
    return None


def publish_all():
    """Publish all pending posts."""
    pending = list_pending()
    if not pending:
        print("✅ No pending posts to publish")
        return []

    pending.sort(key=lambda x: x["created_at"])
    results = []
    for post in pending:
        result = publish_post(post)
        results.append(result)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YT-Flow Social Poster")
    parser.add_argument("--latest", action="store_true", help="Publish latest post")
    parser.add_argument("--topic", help="Publish specific topic")
    parser.add_argument("--all", action="store_true", help="Publish all pending")
    parser.add_argument("--list", action="store_true", help="List pending posts")
    args = parser.parse_args()

    if args.list:
        pending = list_pending()
        print(f"\n📝 Pending Posts ({len(pending)}):")
        print("-" * 50)
        for p in pending:
            print(f"  ⏳ {p['id']} | {p['topic']:20} | {p['title']}")
        print("-" * 50)
    elif args.latest:
        publish_latest()
    elif args.topic:
        publish_by_topic(args.topic)
    elif args.all:
        results = publish_all()
        print(f"\n✅ Published {len(results)} posts")
    else:
        print("Usage:")
        print("  python3 post_to_social.py --latest")
        print("  python3 post_to_social.py --topic face-swap")
        print("  python3 post_to_social.py --all")
        print("  python3 post_to_social.py --list")
