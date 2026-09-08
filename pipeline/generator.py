#!/usr/bin/env python3
"""Marin Pipeline — Story/Advice Generator (LangChain + RAG)

Generates character-specific stories and advice.
Each niche has its own persona prompt and generation style.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from rag.rag_engine import RAGManager
from config import NICHES, FREELLMAPI_URL, FREELLMAPI_KEY, OPENROUTER_API_KEY, OPENROUTER_URL, OLLAMA_BASE_URL

# Google AI Studio key from .env
import os
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_STUDIO", "")


# ── Character System Prompts ─────────────────────────────────────────────────

CHARACTER_PROMPTS = {
    "izuku_midoriya": """You are Izuku Midoriya — a wealthy polymath entrepreneur, spiritual seeker, disciplined athlete, and loving family man. You are in your late 30s, with silver curly hair, a full gray beard, and dark intense eyes. You always wear a black shirt, olive cargo pants, and a black watch.

You are an INXJ — strategic, deep, and intentional. You wake at 5 AM, pray, then conquer the day.

YOUR INTERESTS & KNOWLEDGE:
- Business & Marketing: revenue strategies, negotiation, brand building, consumer psychology
- Religion & Spirituality: temples, mosques, churches, gurdwaras. Bhagavad Gita, Quran, Bible, Stoics
- Psychology & People: MBTI, body language, cognitive biases, motivation
- Markets & Finance: trends, investing, economic thinking
- Fitness & Fighting: gym, football, cricket, boxing, muay thai
- Tech & Learning: Linux, Python, mechatronics, anime, lifelong learning
- Family: cooking with wife, playing with kids, weekend adventures

YOUR VOICE:
- Calm, measured, direct — speak from experience, not theory
- Mix business metaphors with spiritual wisdom
- Reference psychology concepts naturally
- Use tech analogies when explaining things
- Never preachy — share, don't lecture
- End with actionable advice or deep reflection

YOUR DAILY ROUTINE:
- 5 AM: Wake, pray, meditate
- 6 AM: Gym
- 8 AM: Business work
- 12 PM: Visit religious place
- 3 PM: Sports (football/cricket)
- 5 PM: Fighting training
- 7 PM: Study
- 9 PM: Family time

For SHORTS (1-3 lines): Punchy, memorable. Like a truth-slap from someone who's done it all.
For LONGS: Deep breakdowns with real examples from your life.

Generate ONLY the content text. No stage directions. No "Izuku says:" prefix.""",
}

SHORT_PROMPT = """Generate a SHORT video script (1-3 lines max, under 15 seconds of speaking).
This will be overlaid on images with background music.
Make it punchy, memorable, and shareable.

Topic: {topic}
Context from knowledge base:
{rag_context}

Generate:"""

LONG_PROMPT = """Generate a LONG video script (2-5 minutes, detailed story or advice).
This will be narrated with visuals.

Topic: {topic}
Context from knowledge base:
{rag_context}

Generate a compelling, detailed narrative:"""


class StoryGenerator:
    """Generates stories and advice using RAG + LLM."""

    def __init__(self, rag_manager: RAGManager):
        self.rag = rag_manager
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initialize LLM — tries Google Gemini (free), then freellmapi, then ollama."""
        # 1. Google Gemini (free with API key)
        if GOOGLE_AI_KEY:
            print("[Generator] Using Google Gemini")
            return ChatOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=GOOGLE_AI_KEY,
                model="gemini-3.6-flash",
                temperature=0.8,
            )
        # 2. freellmapi
        if FREELLMAPI_KEY:
            return ChatOpenAI(
                base_url=f"{FREELLMAPI_URL}/v1",
                api_key=FREELLMAPI_KEY,
                model="gpt-4o-mini",
                temperature=0.8,
            )
        # 3. OpenRouter
        if OPENROUTER_API_KEY:
            return ChatOpenAI(
                base_url=OPENROUTER_URL,
                api_key=OPENROUTER_API_KEY,
                model="google/gemma-2-9b-it:free",
                temperature=0.8,
            )
        # 4. Ollama
        return ChatOpenAI(
            base_url=f"{OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            model="qwen2.5:1.5b",
            temperature=0.8,
        )

    def generate(
        self,
        niche_id: str,
        topic: str,
        content_type: str = "short",
        instructions: str = "",
        rag_k: int = 5,
    ) -> dict:
        if niche_id not in NICHES:
            raise ValueError(f"Unknown niche: {niche_id}")

        system_prompt = CHARACTER_PROMPTS[niche_id]

        # RAG retrieval
        query = f"{topic} {instructions}".strip()
        rag_results = self.rag.retrieve(niche_id, query, k=rag_k)
        rag_context = "\n\n".join(
            [f"[Source: {r['metadata'].get('source', 'unknown')}]\n{r['text']}" for r in rag_results]
        ) if rag_results else "No specific context found. Generate from character knowledge."

        # Choose template
        prompt_template = SHORT_PROMPT if content_type == "short" else LONG_PROMPT
        user_prompt = prompt_template.format(topic=topic, rag_context=rag_context)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])
        chain = prompt | self.llm | StrOutputParser()

        print(f"[Generator:{niche_id}] Generating {content_type} about: {topic}")
        text = chain.invoke({})

        return {
            "text": text.strip(),
            "niche": niche_id,
            "content_type": content_type,
            "topic": topic,
            "rag_sources": [r["metadata"].get("source", "unknown") for r in rag_results],
        }

    def generate_batch(self, niche_id: str, topics: list[str], content_type: str = "short") -> list[dict]:
        return [self.generate(niche_id, t, content_type) for t in topics]
