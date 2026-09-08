#!/usr/bin/env python3
"""Release a video (simulated or real via platform APIs)."""
import json
import os
import sys
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "release_queue.json")
QUEUE_FILE = os.path.abspath(QUEUE_FILE)

def release(release_id):
    if not os.path.exists(QUEUE_FILE):
        print("❌ No release queue found")
        sys.exit(1)

    with open(QUEUE_FILE) as f:
        queue = json.load(f)

    for i, item in enumerate(queue["queue"]):
        if item["id"] == release_id:
            print(f"🚀 Releasing: {item['id']} → {item['platform']}")
            print(f"   Video: {item['video']}")
            print(f"   Time: {item['scheduled_time']}")
            if item.get("title"):
                print(f"   Title: {item['title']}")

            # Check if video exists
            if not os.path.exists(item["video"]):
                print(f"❌ Video file not found: {item['video']}")
                return False

            # Simulated release — replace with actual API calls
            print(f"\n   [SIMULATED] Uploading to {item['platform']}...")
            print(f"   ✅ Would upload: {os.path.basename(item['video'])}")
            print(f"   📊 File size: {os.path.getsize(item['video']) / 1024 / 1024:.1f} MB")

            # Update status
            item["status"] = "released"
            item["released_at"] = datetime.now().isoformat()
            queue["released"].append(item)
            queue["queue"].pop(i)

            with open(QUEUE_FILE, "w") as f:
                json.dump(queue, f, indent=2)

            print(f"\n✅ {release_id} marked as released")
            return True

    print(f"❌ Release ID not found: {release_id}")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--id":
        print("Usage: python3 release_now.py --id RELEASE-001")
        sys.exit(1)
    release(sys.argv[2])
