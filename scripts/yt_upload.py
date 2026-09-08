#!/usr/bin/env python3
"""
Upload a video to YouTube using OAuth credentials from .env.

Requires in .env:
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN   (obtained via yt_token.py)

Usage:
  python yt_upload.py <video_path> --title "My Video" [--description "..."]
                          [--privacy private|public|unlisted]
                          [--tags "tag1" --tags "tag2"]
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # project root
ENV_FILE = HERE / ".env"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    for k in (
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
    ):
        if k not in env and os.environ.get(k):
            env[k] = os.environ[k]
    return env


def get_credentials(env):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    client_id = env.get("YOUTUBE_CLIENT_ID") or env.get("Client_ID_IZUKU")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET") or env.get("Client_SECRET_IZUKU")
    refresh_token = env.get("YOUTUBE_REFRESH_TOKEN") or env.get("YOUTUBE_REFRESH_TOKEN_IZUKU")

    if not (client_id and client_secret and refresh_token):
        print(
            "[ERROR] Missing YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / "
            "YOUTUBE_REFRESH_TOKEN / YOUTUBE_REFRESH_TOKEN_IZUKU. Run `python yt_token.py` first (authorize once in "
            "the browser), then retry.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    if not creds.valid or not creds.token:
        creds.refresh(Request())
    return creds


def upload(creds, video_path, title, description, tags, privacy):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=1024 * 1024, resumable=True)

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
        notifySubscribers=False,
    )

    print("[UPLOAD] Start (resumable)...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"\n✅ Uploaded!")
    print(f"   Video ID:   {video_id}")
    print(f"   URL:        https://youtu.be/{video_id}")
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube")
    parser.add_argument("video", help="Path to the .mp4 file")
    parser.add_argument("--title", required=True, help="Video title (max 100 chars)")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument(
        "--privacy", default="private", choices=["private", "public", "unlisted"],
        help="Privacy status (default: private)",
    )
    parser.add_argument("--tags", action="append", default=[], help="Tag (repeatable)")
    args = parser.parse_args()

    video_path = Path(args.video).expanduser()
    if not video_path.exists():
        print(f"[ERROR] Video not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    env = load_env()
    creds = get_credentials(env)
    upload(creds, str(video_path), args.title, args.description, args.tags, args.privacy)


if __name__ == "__main__":
    main()