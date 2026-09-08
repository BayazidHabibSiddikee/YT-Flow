# Character Hub

Central source of truth for all AI characters used across pipelines.

## Structure

```
character/
├── README.md              # This file
├── izuku_midoriya.md      # Main character — business, faith, fitness, family
├── faces/                 # Face reference images
│   └── izuku_midoriya.png ← add your face image
├── profiles/              # Extended character profiles
│   └── izuku_midoriya.md
└── templates/             # Prompt templates
    ├── story_short.md
    └── image_gen.md
```

## Active Character

| Character | Niche | Voice | Status |
|-----------|-------|-------|--------|
| Izuku Midoriya | Business, Spirituality, Fitness, Family | Male motivational | Active |

## Content Pillars

1. **Business** — strategies, deals, mindset, wealth building
2. **Spirituality** — multi-faith wisdom, temple visits, meditation
3. **Fitness** — gym, sports, fighting training
4. **Family** — parenting, relationship advice, work-life balance

## Usage

### For Story Generation
Each character `.md` file contains:
- **System prompt** — paste into LLM as system message
- **Voice settings** — TTS config for pipeline
- **Image style** — prompt prefix for image generation
- **Content rules** — what the character can/cannot say

### For Image Generation
Use the `Image Style` section as a prompt prefix:
```
{image_style}, {scene_description}, 4k, cinematic
```

### For Face Swapping
Drop face reference images into `faces/`. Name format: `{character_name}.png`
- Minimum 512x512px
- Front-facing, clear lighting
- Neutral expression preferred

## Adding a New Character

1. Copy `templates/story_short.md` as starting point
2. Fill in all sections
3. Add face image to `faces/`
4. Add extended profile to `profiles/`
5. Register in pipeline `config.py`
