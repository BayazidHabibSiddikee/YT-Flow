#!/usr/bin/env python3
"""
YT-Flow: Release Scheduler
===========================
Manage video release queue with platform tracking and cron integration.
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
QUEUE_FILE = os.path.join(PROJECT_DIR, "logs", "release_queue.json")


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return {"queue": [], "released": []}


def save_queue(data):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_to_queue(video_path, platform, schedule_time, title="", description=""):
    queue = load_queue()
    entry = {
        "id": f"RELEASE-{len(queue['queue']) + len(queue['released']) + 1:03d}",
        "video": video_path,
        "platform": platform,
        "scheduled_time": schedule_time,
        "title": title,
        "description": description,
        "status": "scheduled",
        "created_at": datetime.now().isoformat(),
    }
    queue["queue"].append(entry)
    save_queue(queue)
    print(f"✅ Added: {entry['id']} → {platform} @ {schedule_time}")
    return entry


def list_queue():
    queue = load_queue()
    print("\n📋 Release Queue:")
    print("-" * 70)
    for item in queue["queue"]:
        vname = os.path.basename(item["video"])
        print(f"  [{item['status']:^10}] {item['id']} | {item['platform']:10} | {item['scheduled_time']} | {vname}")
    if not queue["queue"]:
        print("  (empty)")
    print(f"\n📤 Released: {len(queue['released'])}")
    print("-" * 70)


def generate_cron():
    queue = load_queue()
    print("\n# Add to crontab (crontab -e):")
    print("#" * 50)
    for item in queue["queue"]:
        if item["status"] != "scheduled":
            continue
        try:
            dt = datetime.fromisoformat(item["scheduled_time"])
            ct = f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"
            script = os.path.join(SCRIPT_DIR, "release_now.py")
            print(f'{ct} python3 {script} --id {item["id"]}')
        except Exception as e:
            print(f"# ERROR: {item['id']}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 schedule_release.py add --video PATH --platform PLATFORM --time ISO [--title T] [--desc D]")
        print("  python3 schedule_release.py list")
        print("  python3 schedule_release.py cron")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_queue()
    elif cmd == "cron":
        generate_cron()
    elif cmd == "add":
        parser = argparse.ArgumentParser()
        parser.add_argument("--video", required=True)
        parser.add_argument("--platform", required=True)
        parser.add_argument("--time", required=True)
        parser.add_argument("--title", default="")
        parser.add_argument("--desc", default="")
        args = parser.parse_args(sys.argv[2:])
        add_to_queue(args.video, args.platform, args.time, args.title, args.desc)
