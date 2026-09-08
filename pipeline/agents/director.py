#!/usr/bin/env python3
"""Director Agent — Reviews content ideas, approves/rejects, gives direction.

The Director checks:
1. Is the idea good? Will it get views?
2. Is the topic trending or evergreen?
3. What's the best angle to make it go viral?
4. What images/style should be used?
5. Final go/no-go for production.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

import os
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_STUDIO", "")


DIRECTOR_SYSTEM = """You are the Director — a content strategist who decides what videos get made.

Your job is to REVIEW content ideas and give a clear verdict:
- APPROVE: The idea is solid, will get views
- REVISE: The idea needs tweaking (suggest changes)
- REJECT: The idea won't work (explain why)

You think like a YouTube algorithm expert AND a content creator. You know what gets:
- Clicks (thumbnails, titles)
- Watch time (hooks, pacing)
- Shares (emotional resonance)
- subscribers (consistent value)

RULES:
1. Be brutally honest. Bad ideas waste time and money.
2. If REVISE, give specific actionable changes.
3. If APPROVE, suggest the best angle, hook, and visual style.
4. Consider: Is this searchable? Is this shareable? Is this bingeable?
5. Rate virality potential 1-10.

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "verdict": "APPROVE" | "REVISE" | "REJECT",
    "score": 1-10,
    "hook": "The first 3 seconds that grab attention",
    "angle": "Best angle to make this go viral",
    "images": ["scene 1 description", "scene 2 description", "scene 3 description"],
    "style": "visual style recommendation",
    "title_suggestion": "YouTube title that gets clicks",
    "tags": ["tag1", "tag2", "tag3"],
    "reasoning": "Why this verdict",
    "changes_if_revise": "What to change (empty if APPROVE)"
}}"""


class DirectorAgent:
    """Reviews content ideas and gives direction."""

    def __init__(self):
        self.llm = self._init_llm()

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

    def review(self, idea: dict) -> dict:
        """
        Review a content idea.
        idea = {"topic": "...", "text": "...", "niche": "...", "content_type": "short"}
        Returns verdict with direction.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECTOR_SYSTEM),
            ("human", """Review this content idea:

Topic: {topic}
Niche: {niche}
Content Type: {content_type}

Draft Text:
{text}

Give your verdict and direction."""),
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "topic": idea["topic"],
            "niche": idea["niche"],
            "content_type": idea.get("content_type", "short"),
            "text": idea.get("text", ""),
        })

        # Parse JSON from response
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"verdict": "APPROVE", "score": 5, "reasoning": response}
        except json.JSONDecodeError:
            result = {"verdict": "APPROVE", "score": 5, "reasoning": response}

        print(f"[Director] Verdict: {result.get('verdict', '?')} | Score: {result.get('score', '?')}/10")
        return result
