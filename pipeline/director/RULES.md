# Director Pipeline — Video Editing Instructions for AI Agents

## Purpose
This directory contains the rules, templates, and workflows that AI editors (opencode/claude/cline) follow when processing raw videos from the pipeline.

**The raw video is NOT the final product.** The director pipeline transforms raw clips into engaging, platform-ready content.

---

## Pipeline Flow

```
Raw Video → Director Analysis → Editing Instructions → Agent Edits → Final Video
```

1. **Director** reads the raw video metadata, story text, and audio
2. **Director** generates a detailed editing brief
3. **Editor Agent** follows the brief to produce final video
4. **Quality Check** validates the result

---

## Editing Rules

### 1. Subtitles
- **ALWAYS** present — no video goes out without captions
- Font: Arial Regular (not bold)
- Size: 12px (minimal, almost invisible)
- Color: Semi-transparent white (80% opacity)
- BorderStyle=4 (no background box)
- Outline=0, Shadow=0
- Position: Bottom center, MarginV=40
- Max 25 characters per line (vertical)
- Each subtitle: 3 seconds display time
- Should be barely visible — image is the focus

### 2. Transitions
- **Crossfade** between scenes (0.5s duration)
- **Fade to black** between major sections
- **No hard cuts** — every transition must be smooth
- Ken Burns effect on still images (slow zoom/pan)

### 3. Pacing
- **Shorts (9:16):** 15-30 seconds max
- **Longs (16:9):** 2-5 minutes
- First 3 seconds: hook (most engaging visual + text)
- Last 3 seconds: call to action or cliffhanger
- Never let a single image sit for more than 5 seconds

### 4. Visual Effects
- **Color grading:** Warm tones for war stories, cool for gym, golden for spiritual
- **Vignette:** Subtle dark edges to focus attention
- **Film grain:** Light grain for cinematic feel (optional)
- **Speed ramp:** Slow motion for dramatic moments

### 5. Audio
- Background music: Low volume (-20dB), match the niche mood
- Voice: Clear, no music competing with narration
- Sound effects: Subtle whooshes on transitions (optional)
- Normalize audio to -14 LUFS

### 6. Branding
- Watermark: Small, corner position, semi-transparent
- Intro: 1-2 seconds max (logo + niche name)
- Outro: Subscribe/follow prompt (3 seconds)
- Consistent color palette per niche

---

## Niche-Specific Styles

### Izuku Midoriya (War Stories)
- **Color:** Desaturated, warm shadows, orange highlights (fire)
- **Font weight:** Heavy, impactful
- **Transitions:** Slow crossfades, fade to black
- **Mood:** Somber, reflective, powerful
- **Background music:** Orchestral, ambient war sounds

### Gym Mentality
- **Color:** High contrast, dark shadows, bright highlights
- **Font weight:** Bold, aggressive
- **Transitions:** Quick cuts, glitch effects
- **Mood:** Intense, motivating, raw
- **Background music:** Hip-hop, trap, electronic

### Krishna Religious
- **Color:** Warm golden, soft light, ethereal
- **Font weight:** Medium, elegant
- **Transitions:** Slow dissolves, light leaks
- **Mood:** Peaceful, wise, divine
- **Background music:** Ambient, sitar, soft piano

---

## Director Brief Template

```json
{
  "video_id": "unique_id",
  "niche": "izuku_midoriya",
  "content_type": "short",
  "duration": 25,
  "story_text": "full narration text",
  "scenes": [
    {
      "scene_number": 1,
      "description": "Old man by campfire",
      "image": "path/to/image.jpg",
      "audio_segment": "0.0-5.0s",
      "subtitle": "The night before the battle...",
      "effect": "slow_zoom_in",
      "transition": "crossfade_0.5s"
    }
  ],
  "color_grading": "warm_desaturated",
  "font": "Montserrat-Bold",
  "music": "ambient_orchestral",
  "music_volume_db": -20,
  "output_format": "9:16",
  "platform": "youtube_shorts"
}
```

---

## Quality Checklist

Before marking a video as complete, verify:

- [ ] Subtitles present and synced
- [ ] No hardcoded text overlapping subtitles
- [ ] Audio normalized (-14 LUFS)
- [ ] Music doesn't compete with voice
- [ ] Transitions smooth (no hard cuts)
- [ ] First 3 seconds hook the viewer
- [ ] Last 3 seconds have CTA/cliffhanger
- [ ] Resolution: 1080x1920 (shorts) or 1920x1080 (longs)
- [ ] File size reasonable (<50MB)
- [ ] Duration within platform limits

---

## Agent Instructions

When you receive a video to edit:

1. **Read this RULES.md** first
2. **Read the niche CHARACTER.md** for style guidance
3. **Generate the director brief** using the template above
4. **Apply edits** following the brief exactly
5. **Run the quality checklist** before saving
6. **Output** to `output/shorts/` or `output/longs/` with `_edited` suffix

**NEVER skip subtitles. NEVER use hard cuts. ALWAYS follow the niche style.**
