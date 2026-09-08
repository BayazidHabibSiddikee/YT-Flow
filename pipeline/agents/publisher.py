#!/usr/bin/env python3
"""Publisher Agent — Posts videos to YouTube and social media.

Handles:
1. YouTube Shorts upload (via yt-dlp / YouTube API)
2. YouTube description, tags, thumbnails
3. Social media cross-posting
4. Scheduling
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

import os
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_STUDIO", "")


PUBLISHER_SYSTEM = """You are the Publisher — you prepare videos for YouTube and social media.

For each video, generate:

1. **YouTube Upload Package:**
   - Title (max 100 chars, SEO optimized, click-worthy)
   - Description (2-3 paragraphs with keywords, hashtags)
   - Tags (15-20 relevant tags)
   - Category selection
   - Thumbnail text suggestions

2. **Social Media Captions:**
   - Instagram (with hashtags)
   - Twitter/X (thread format, 2-3 tweets)
   - TikTok caption
   - LinkedIn (professional angle)

3. **SEO Notes:**
   - Primary keyword
   - Secondary keywords
   - Best upload time
   - Competitor analysis notes

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "youtube": {{
        "title": "...",
        "description": "...",
        "tags": ["tag1", "tag2"],
        "category": "People & Blogs",
        "thumbnail_text": ["line 1", "line 2"]
    }},
    "social": {{
        "instagram": "...",
        "twitter": ["tweet 1", "tweet 2"],
        "tiktok": "...",
        "linkedin": "..."
    }},
    "seo": {{
        "primary_keyword": "...",
        "secondary_keywords": ["..."],
        "best_time": "..."
    }}
}}"""


class PublisherAgent:
    """Preares and publishes content to platforms."""

    def __init__(self):
        self.llm = self._init_llm()
        self.youtube_token = os.getenv("YOUTUBE_REFRESH_TOKEN_IZUKU", "")
        self.client_id = os.getenv("Client_ID_IZUKU", "")
        self.client_secret = os.getenv("Client_SECRET_IZUKU", "")

    def _init_llm(self):
        if GOOGLE_AI_KEY:
            return ChatOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=GOOGLE_AI_KEY,
                model="gemini-3.6-flash",
                temperature=0.7,
            )
        from config import FREELLMAPI_URL, FREELLMAPI_KEY
        return ChatOpenAI(
            base_url=f"{FREELLMAPI_URL}/v1",
            api_key=FREELLMAPI_KEY,
            model="gpt-4o-mini",
            temperature=0.7,
        )

    def prepare_upload(self, video_meta: dict) -> dict:
        """
        Prepare upload package for a video.
        Returns YouTube metadata + social captions.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", PUBLISHER_SYSTEM),
            ("human", """Prepare upload package for this video:

Topic: {topic}
Niche: {niche}
Content Type: {content_type}

Script:
{text}

Generate the full upload package."""),
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "topic": video_meta.get("topic", ""),
            "niche": video_meta.get("niche", ""),
            "content_type": video_meta.get("content_type", "short"),
            "text": video_meta.get("text", ""),
        })

        # Parse JSON
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"youtube": {}, "social": {}, "seo": {}}
        except json.JSONDecodeError:
            result = {"youtube": {}, "social": {}, "seo": {}}

        print(f"[Publisher] Title: {result.get('youtube', {}).get('title', 'N/A')}")
        return result

    def upload_to_youtube(self, video_path: Path, metadata: dict, auto_upload: bool = True) -> dict:
        """Upload video to YouTube via OAuth. Returns result dict."""
        if not self.youtube_token:
            print("[Publisher] No YouTube token — skipping upload")
            return {"status": "skipped", "reason": "no_token"}

        if not auto_upload:
            print("[Publisher] Auto-upload disabled — saving metadata only")
            return self._save_upload_meta(video_path, metadata)

        yt_meta = metadata.get("youtube", {})
        title = yt_meta.get("title", "Izuku Midoriya — Business Wisdom")
        description = yt_meta.get("description", "")
        tags = yt_meta.get("tags", [])
        privacy = yt_meta.get("privacyStatus", "unlisted")

        print(f"[Publisher] Uploading to YouTube: {title}")
        print(f"[Publisher] Video: {video_path} ({video_path.stat().st_size//1024//1024}MB)")

        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))

        for attempt in range(2):
            try:
                from yt_upload import get_credentials, upload as _yt_upload

                env = {
                    "YOUTUBE_CLIENT_ID": self.client_id,
                    "YOUTUBE_CLIENT_SECRET": self.client_secret,
                    "YOUTUBE_REFRESH_TOKEN": self.youtube_token,
                }

                creds = get_credentials(env)
                video_id = _yt_upload(creds, str(video_path), title, description, tags, privacy)
                result = {"status": "uploaded", "video_id": video_id, "url": f"https://youtu.be/{video_id}"}
                print(f"[Publisher] ✅ Uploaded: {result['url']}")
                return result
            except Exception as e:
                print(f"[Publisher] ❌ Upload attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    import time
                    time.sleep(2)

        return {"status": "error", "error": "Upload failed after 2 attempts"}

    def _save_upload_meta(self, video_path: Path, metadata: dict) -> dict:
        upload_dir = Path("output/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        meta_path = upload_dir / f"upload_{ts}.json"
        meta_path.write_text(json.dumps({
            "video": str(video_path),
            "metadata": metadata,
            "timestamp": ts,
            "status": "ready_to_upload",
        }, indent=2))
        return {"status": "saved", "meta_path": str(meta_path)}

    def save_social_captions(self, metadata: dict, video_meta: dict) -> Path:
        """Save social media captions to a file for manual posting."""
        social = metadata.get("social", {})
        topic = video_meta.get("topic", "unknown")

        captions_dir = Path("output/captions")
        captions_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        caption_path = captions_dir / f"captions_{ts}.md"

        content = f"""# Social Media Captions — {topic}
Generated: {datetime.now().isoformat()}

## YouTube
**Title:** {metadata.get('youtube', {}).get('title', '')}
**Description:**
{metadata.get('youtube', {}).get('description', '')}

**Tags:** {', '.join(metadata.get('youtube', {}).get('tags', []))}

---

## Instagram
{social.get('instagram', '')}

---

## Twitter/X
"""
        for tweet in social.get('twitter', []):
            content += f"{tweet}\n\n---\n\n"

        content += f"""## TikTok
{social.get('tiktok', '')}

---

## LinkedIn
{social.get('linkedin', '')}
"""
        caption_path.write_text(content)
        print(f"[Publisher] Captions saved: {caption_path}")
        return caption_path
