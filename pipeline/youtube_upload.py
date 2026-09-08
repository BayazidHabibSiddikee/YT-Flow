#!/usr/bin/env python3
"""Upload YouTube Shorts via YouTube Data API v3 with OAuth 2.0.

Usage:
    python youtube_upload.py pipeline/output/deku_fitness_final.mp4 \
        --title "Discipline Is Not A Punishment #Shorts" \
        --description "..." \
        --tags "motivation,fitness,shorts" \
        --privacy public
"""

import os
import sys
import json
import argparse
import base64
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange refresh token for access token."""
    data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()

    req = Request(TOKEN_URL, data=data, method="POST")
    with urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["access_token"]


def upload_video(
    access_token: str,
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "public",
    category_id: str = "22",
) -> dict:
    """Upload video to YouTube using resumable upload."""
    file_size = os.path.getsize(video_path)

    # Initiate resumable upload
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    init_body = json.dumps(metadata).encode()
    init_url = f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status"

    init_req = Request(init_url, data=init_body, method="POST")
    init_req.add_header("Authorization", f"Bearer {access_token}")
    init_req.add_header("Content-Type", "application/json; charset=UTF-8")
    init_req.add_header("X-Upload-Content-Type", "video/mp4")
    init_req.add_header("X-Upload-Content-Length", str(file_size))

    with urlopen(init_req) as resp:
        upload_url = resp.headers.get("Location")

    if not upload_url:
        raise RuntimeError("Failed to initiate resumable upload")

    # Upload the video file
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_req = Request(upload_url, data=video_data, method="PUT")
    upload_req.add_header("Content-Type", "video/mp4")
    upload_req.add_header("Content-Length", str(file_size))

    with urlopen(upload_req) as resp:
        result = json.loads(resp.read())

    return result


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube Shorts")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"])
    parser.add_argument("--category", default="22", help="YouTube category ID (22=People & Blogs)")
    parser.add_argument("--client-id", default=os.getenv("Client_ID_IZUKU"))
    parser.add_argument("--client-secret", default=os.getenv("Client_SECRET_IZUKU"))
    parser.add_argument("--refresh-token", default=os.getenv("YOUTUBE_REFRESH_TOKEN_IZUKU"))
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("ERROR: Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env")
        print("Get these from https://console.cloud.google.com/apis/credentials")
        sys.exit(1)

    if not args.refresh_token:
        print("ERROR: Set YOUTUBE_REFRESH_TOKEN_IZUKU in .env")
        sys.exit(1)

    if not os.path.exists(args.video):
        print(f"ERROR: Video not found: {args.video}")
        sys.exit(1)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    print(f"Getting access token...")
    token = get_access_token(args.client_id, args.client_secret, args.refresh_token)
    print(f"Access token obtained")

    print(f"Uploading: {args.video}")
    print(f"Title: {args.title}")
    result = upload_video(
        access_token=token,
        video_path=args.video,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy=args.privacy,
        category_id=args.category,
    )

    video_id = result.get("id", "unknown")
    print(f"\nUpload complete!")
    print(f"Video ID: {video_id}")
    print(f"URL: https://youtube.com/shorts/{video_id}")

    return result


if __name__ == "__main__":
    main()
