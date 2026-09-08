#!/usr/bin/env python3
"""YT-Flow: Release a video from the queue."""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
QUEUE_FILE = os.path.join(PROJECT_DIR, "logs", "release_queue.json")


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
            if not os.path.exists(item["video"]):
                print(f"❌ Video not found: {item['video']}")
                return False

            size_mb = os.path.getsize(item["video"]) / 1024 / 1024
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   [SIMULATED] Upload to {item['platform']}")

            item["status"] = "released"
            item["released_at"] = datetime.now().isoformat()
            queue["released"].append(item)
            queue["queue"].pop(i)

            with open(QUEUE_FILE, "w") as f:
                json.dump(queue, f, indent=2)
            print(f"✅ {release_id} released")
            return True

    print(f"❌ ID not found: {release_id}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--id":
        print("Usage: python3 release_now.py --id RELEASE-001")
        sys.exit(1)
    release(sys.argv[2])
