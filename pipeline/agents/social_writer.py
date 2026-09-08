#!/usr/bin/env python3
"""Social Writer Agent — Izuku writes posts for different platforms.

Izuku's voice: calm, confident, direct. Shares business wisdom,
spiritual insights, fitness motivation, and family values.
Writes like a wealthy polymath who's done it all.
"""

import json
from pathlib import Path
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

import os
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_STUDIO", "")


SOCIAL_WRITER_SYSTEM = """You are Izuku Midoriya — a wealthy polymath entrepreneur, spiritual seeker,
and family man. You write social media posts that share your daily wisdom.

Your voice: Calm, confident, direct. Never preachy. You share from experience.

You write about: business, marketing, psychology, religion, fitness, fighting, family.

RULES:
1. Write like a person, not a brand
2. Share real insights, not platitudes
3. Be specific — reference real experiences
4. End with something memorable
5. Each platform has different vibes:

**Instagram:** Visual caption. 3-5 lines. Hashtags at end.
**Twitter/X:** Punchy thread. 2-3 tweets max. Each tweet standalone.
**TikTok:** Casual, relatable. Like talking to a friend.
**LinkedIn:** Professional angle. Business lesson. Thought leadership.

Write as if you just experienced something and want to share it.

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "instagram": "post caption with #hashtags",
    "twitter": ["tweet 1", "tweet 2", "tweet 3"],
    "tiktok": "casual caption",
    "linkedin": "professional post",
    "one_liner": "a standalone quote/post that works anywhere"
}}"""


class SocialWriter:
    """Izuku writes social media posts."""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        if GOOGLE_AI_KEY:
            return ChatOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=GOOGLE_AI_KEY,
                model="gemini-3.6-flash",
                temperature=0.8,
            )
        from config import FREELLMAPI_URL, FREELLMAPI_KEY
        return ChatOpenAI(
            base_url=f"{FREELLMAPI_URL}/v1",
            api_key=FREELLMAPI_KEY,
            model="gpt-4o-mini",
            temperature=0.8,
        )

    def write_posts(self, video_meta: dict) -> dict:
        """
        Write social media posts for a video.
        video_meta = {"topic": "...", "text": "...", "niche": "..."}
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SOCIAL_WRITER_SYSTEM),
            ("human", """Write social media posts for this content:

Topic: {topic}
Niche: {niche}

Video script/text:
{text}

Write posts for all platforms."""),
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "topic": video_meta.get("topic", ""),
            "niche": video_meta.get("niche", ""),
            "text": video_meta.get("text", ""),
        })

        # Parse JSON
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"one_liner": response[:200]}
        except json.JSONDecodeError:
            result = {"one_liner": response[:200]}

        print(f"[SocialWriter] One-liner: {result.get('one_liner', 'N/A')[:60]}...")
        return result

    def save_posts(self, posts: dict, video_meta: dict) -> Path:
        """Save posts to file for review."""
        posts_dir = Path("output/posts")
        posts_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        post_path = posts_dir / f"posts_{ts}.md"

        topic = video_meta.get("topic", "unknown")
        content = f"""# Social Posts — {topic}
Generated: {datetime.now().isoformat()}

## Instagram
{posts.get('instagram', '')}

---

## Twitter/X
"""
        for tweet in posts.get('twitter', []):
            content += f"{tweet}\n\n"

        content += f"""
---

## TikTok
{posts.get('tiktok', '')}

---

## LinkedIn
{posts.get('linkedin', '')}

---

## One-Liner (works anywhere)
> {posts.get('one_liner', '')}
"""
        post_path.write_text(content)
        print(f"[SocialWriter] Posts saved: {post_path}")
        return post_path
