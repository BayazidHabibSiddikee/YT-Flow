# Video Editor Agent

## Purpose
Transform raw pipeline videos into platform-ready content by following the Director Pipeline rules.

## How to Use
```bash
# Edit a short video
python3 agents/video_editor.py edit output/shorts/izuku_midoriya_20260905_143652.mp4 --niche izuku_midoriya

# Edit with custom brief
python3 agents/video_editor.py edit video.mp4 --brief director_brief.json
```

## Agent Instructions

When you receive a video to edit, follow these steps:

### Step 1: Analyze Raw Video
```python
import subprocess
result = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path], capture_output=True, text=True)
metadata = json.loads(result.stdout)
```

Extract:
- Duration
- Resolution
- Audio streams
- Video streams

### Step 2: Read Context Files
- `director/RULES.md` — editing rules
- `niches/{niche}/CHARACTER.md` — niche style
- Story text from pipeline output

### Step 3: Generate Director Brief
Create JSON brief with scene-by-scene instructions:

```json
{
  "video_id": "unique_id",
  "niche": "izuku_midoriya",
  "content_type": "short",
  "duration": 25,
  "scenes": [
    {
      "scene_number": 1,
      "start": 0.0,
      "end": 5.0,
      "image": "path/to/image.jpg",
      "subtitle": "The night before the battle...",
      "effect": "slow_zoom_in",
      "transition": "crossfade_0.5s"
    }
  ],
  "color_grading": "warm_desaturated",
  "font": "Montserrat-Bold",
  "music": "ambient_orchestral",
  "music_volume_db": -20
}
```

### Step 4: Apply Edits

#### Subtitles (ALWAYS)
```python
# Generate SRT from story text
def text_to_srt(text, output_path, chars_per_line=35):
    words = text.split()
    lines, current, cur_len = [], [], 0
    for word in words:
        if cur_len + len(word) + 1 > chars_per_line and current:
            lines.append(" ".join(current))
            current, cur_len = [word], len(word)
        else:
            current.append(word)
            cur_len += len(word) + 1
    if current:
        lines.append(" ".join(current))

    entries = []
    for i, line in enumerate(lines):
        start = i * 2.5
        end = start + 2.5
        entries.append(f"{i+1}\n{fmt_srt(start)} --> {fmt_srt(end)}\n{line}\n")

    Path(output_path).write_text("\n".join(entries))
```

#### Burn Subtitles
```python
style = (
    "FontName=Montserrat Bold,FontSize=28,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,BorderStyle=3,Outline=3,Shadow=0,"
    "Alignment=2,MarginV=80,Bold=1"
)
cmd = [
    "ffmpeg", "-y", "-i", str(video_path),
    "-vf", f"subtitles={srt_path}:force_style='{style}'",
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "copy", "-movflags", "+faststart",
    str(output_path),
]
```

#### Ken Burns Effect
```python
# Slow zoom on image
zoom_filter = (
    f"scale=8000:-1,zoompan=z='min(zoom+0.001,1.5)':"
    f"d={duration*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
)
```

#### Color Grading
```python
# Warm desaturated for war stories
color_filter = "eq=saturation=0.7:contrast=1.1:brightness=0.05"

# High contrast for gym
color_filter = "eq=saturation=1.3:contrast=1.4:brightness=-0.05"

# Warm golden for spiritual
color_filter = "eq=saturation=0.9:contrast=1.1:colorbalance=rs=0.1:gs=0.05:bs=-0.1"
```

### Step 5: Quality Checklist

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

### Step 6: Output
Save to `output/shorts/{niche}_{timestamp}_edited.mp4`

## FFmpeg Commands Reference

### Basic subtitle burn
```bash
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3'" -c:v libx264 -preset fast -crf 23 -c:a copy output.mp4
```

### Ken Burns + subtitles
```bash
ffmpeg -loop 1 -i image.jpg -i audio.wav -vf "scale=8000:-1,zoompan=z='min(zoom+0.001,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,subtitles=subs.srt" -c:v libx264 -preset fast -crf 23 -c:a aac -shortest output.mp4
```

### Color grade + subtitles
```bash
ffmpeg -i input.mp4 -vf "eq=saturation=0.7:contrast=1.1,subtitles=subs.srt" -c:v libx264 -preset fast -crf 23 -c:a copy output.mp4
```

### Normalize audio
```bash
ffmpeg -i input.mp4 -af "loudnorm=I=-14:TP=-1:LRA=11" -c:v copy output.mp4
```
