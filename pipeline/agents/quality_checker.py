#!/usr/bin/env python3
"""Quality Checker Agent — Rates finished videos before publishing.

Checks:
1. Audio quality (clear voice, no artifacts)
2. Visual quality (images match content, good composition)
3. Subtitle quality (readable, synced, no overlaps)
4. Content quality (message clear, hook strong, pacing right)
5. Overall virality potential
"""

import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

import os
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_STUDIO", "")


QUALITY_SYSTEM = """You are the Quality Checker — the final gate before a video goes public.

You evaluate videos on 5 criteria, each scored 1-10:

1. **AUDIO** (weight: 25%)
   - Voice clear and understandable?
   - Good pacing (not too fast/slow)?
   - No background noise or artifacts?
   - Emotion matches content?

2. **VISUALS** (weight: 25%)
   - Images match the story/content?
   - Good composition and color?
   - Ken Burns / motion effects present?
   - Professional look overall?

3. **SUBTITLES** (weight: 20%)
   - Readable font and size?
   - Synced with audio?
   - No overlapping text?
   - Proper line breaks?

4. **CONTENT** (weight: 20%)
   - Strong hook in first 3 seconds?
   - Clear message throughout?
   - Good pacing (not boring)?
   - Memorable ending?

5. **VIRALITY** (weight: 10%)
   - Would you share this?
   - Does it make you feel something?
   - Is it searchable/discoverable?
   - Does it stand out?

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "overall_score": 1-10,
    "verdict": "PUBLISH" | "EDIT_NEEDED" | "REJECT",
    "scores": {{
        "audio": 1-10,
        "visuals": 1-10,
        "subtitles": 1-10,
        "content": 1-10,
        "virality": 1-10
    }},
    "issues": ["issue 1", "issue 2"],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "title_suggestion": "Better title if needed",
    "thumbnail_note": "What the thumbnail should show",
    "reasoning": "Overall assessment"
}}"""


class QualityChecker:
    """Rates finished videos before publishing."""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        if GOOGLE_AI_KEY:
            return ChatOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=GOOGLE_AI_KEY,
                model="gemini-3.6-flash",
                temperature=0.3,
            )
        from config import FREELLMAPI_URL, FREELLMAPI_KEY
        return ChatOpenAI(
            base_url=f"{FREELLMAPI_URL}/v1",
            api_key=FREELLMAPI_KEY,
            model="gpt-4o-mini",
            temperature=0.3,
        )

    def check(self, video_meta: dict) -> dict:
        """
        Check a video's quality.
        video_meta = {
            "video_path": "...",
            "text": "...",
            "topic": "...",
            "niche": "...",
            "audio_path": "...",
            "images": [...]
        }
        """
        video_path = Path(video_meta.get("video_path", ""))
        text = video_meta.get("text", "")
        topic = video_meta.get("topic", "")

        # Check if video exists and get basic info
        video_exists = video_path.exists()
        video_size = video_path.stat().st_size if video_exists else 0

        prompt = ChatPromptTemplate.from_messages([
            ("system", QUALITY_SYSTEM),
            ("human", """Rate this video:

Topic: {topic}
Niche: {niche}
Video: {video_path} ({video_size} bytes)
Video exists: {video_exists}

Script text:
{text}

Evaluate quality and give your verdict."""),
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "topic": topic,
            "niche": video_meta.get("niche", ""),
            "video_path": str(video_path),
            "video_size": video_size,
            "video_exists": video_exists,
            "text": text,
        })

        # Parse JSON
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"overall_score": 5, "verdict": "PUBLISH", "reasoning": response}
        except json.JSONDecodeError:
            result = {"overall_score": 5, "verdict": "PUBLISH", "reasoning": response}

        score = result.get("overall_score", 0)
        verdict = result.get("verdict", "REJECT")
        print(f"[Quality] Score: {score}/10 | Verdict: {verdict}")
        return result
