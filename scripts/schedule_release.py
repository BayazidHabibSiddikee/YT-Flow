#!/usr/bin/env python3
"""
YT-Flow Release Scheduler
Manages video release queue with platform tracking and cron integration.
"""
import json
import os
import sys
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "release_queue.json")
QUEUE_FILE = os.path.abspath(QUEUE_FILE)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return {"queue": [], "released": []}

def save_queue(data):
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
    print(f"✅ Added to queue: {entry['id']} → {platform} @ {schedule_time}")
    return entry

def list_queue():
    queue = load_queue()
    print("\n📋 Release Queue:")
    print("-" * 60)
    for item in queue["queue"]:
        print(f"  [{item['status'].upper():^10}] {item['id']} | {item['platform']:10} | {item['scheduled_time']} | {os.path.basename(item['video'])}")
    if not queue["queue"]:
        print("  (empty)")
    print(f"\n📤 Released: {len(queue['released'])}")
    print("-" * 60)

def generate_cron():
    """Generate crontab entries for scheduled releases."""
    queue = load_queue()
    print("\n# Add these to your crontab (crontab -e):")
    print("#" * 50)
    for item in queue["queue"]:
        if item["status"] != "scheduled":
            continue
        try:
            dt = datetime.fromisoformat(item["scheduled_time"])
            cron_time = f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"
            script = os.path.join(os.path.dirname(__file__), "release_now.py")
            print(f'{cron_time} python3 {script} --id {item["id"]}  # {item["platform"]} - {os.path.basename(item["video"])}')
        except Exception as e:
            print(f"# ERROR parsing time for {item['id']}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 schedule_release.py add --video PATH --platform PLATFORM --time ISO_TIME [--title TITLE] [--desc DESC]")
        print("  python3 schedule_release.py list")
        print("  python3 schedule_release.py cron")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_queue()
    elif cmd == "cron":
        generate_cron()
    elif cmd == "add":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--video", required=True)
        parser.add_argument("--platform", required=True)
        parser.add_argument("--time", required=True)
        parser.add_argument("--title", default="")
        parser.add_argument("--desc", default="")
        args = parser.parse_args(sys.argv[2:])
        add_to_queue(args.video, args.platform, args.time, args.title, args.desc)
