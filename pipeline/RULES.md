# Pipeline Rules — ALWAYS FOLLOW

## Subtitles
- **ALWAYS** burn subtitles into every video
- Use Arial Bold, white text, black outline (3px)
- Font size 28pt for vertical (9:16), 24pt for horizontal (16:9)
- MarginV=80 (bottom center)
- Max 35 chars per line for vertical, 50 for horizontal
- Each subtitle line shows for 2.5 seconds
- SRT format, auto-generated from story text

## Images
- **PRIMARY:** FAL API (high quality, cinematic)
- **FALLBACK:** Pollinations.ai (free, decent)
- Resolution: 1080x1920 (vertical shorts)
- Style: cinematic, dramatic lighting, 4k quality
- Generate 5 images per short, 10 per long
- Scene descriptions from story paragraphs

## Voice / TTS
- **PRIMARY:** VibeVoice-Realtime-0.5B via Kaggle GPU (free T4)
- **FALLBACK:** edge-tts (immediate, lower quality)
- Voice assignments:
  - Izuku Midoriya: old_man (deep, slow, -15% rate)
  - Gym Mentality: male_motivational (strong, direct)
  - Krishna Religious: female_calm (peaceful, gentle)
- Always generate .wav for VibeVoice, .mp3 for edge-tts

## Video Generation
- **SHORTS (9:16):** Images + audio + burned subtitles
- **LONGS (16:9):** Images + audio + burned subtitles
- AI video (HF/Kaggle/MiniMax) when available
- FFmpeg always works as fallback
- Duration: 4s per image (shorts), 6s per image (longs)

## Story Generation
- Use Gemini (Google AI Studio) as primary LLM
- RAG context from niche's rag/data/ directory
- Character voice must match persona
- Shorts: 1-3 lines, punchy, memorable
- Longs: detailed, narrative, 2-5 minutes

## Output
- Shorts: output/shorts/{niche}_{timestamp}.mp4
- Longs: output/longs/{niche}_long_{timestamp}.mp4
- Always include: story text, audio, video in editor queue
- Video goes to editor (opencode/claude/cline) for final polish
