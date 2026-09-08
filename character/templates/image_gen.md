# Image Generation Prompt Template

## Base Format

```
{character_image_style}, {scene_description}, {lighting}, {quality}
```

## Examples

### Izuku Midoriya — Campfire Scene
```
cinematic anime style, elderly Japanese war veteran sitting by campfire,
deep wrinkles, wise tired eyes, battlefield ruins background,
dramatic orange firelight, dark moody atmosphere, emotional detailed face,
4k quality, film grain
```

### Gym Coach — Training Scene
```
cinematic dark gym scene, muscular silhouette lifting heavy weight,
dramatic spotlight, sweat drops, iron and steel equipment,
high contrast lighting, intense focus, motivational atmosphere,
4k quality, film grain
```

### Krishna Teacher — Temple Scene
```
cinematic spiritual scene, serene woman in meditation pose,
divine golden light, temple interior, incense smoke wisps,
warm ethereal glow, sacred atmosphere, lotus flowers,
4k quality, soft focus
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{character_image_style}` | From character .md file | `cinematic anime style, elderly Japanese war veteran` |
| `{scene_description}` | What's happening | `sitting by campfire, telling story` |
| `{lighting}` | Light quality | `dramatic orange firelight` |
| `{quality}` | Resolution/detail | `4k quality, film grain` |

## Aspect Ratios

- **Shorts (9:16):** 1080x1920
- **Longs (16:9):** 1920x1080
- **Square (1:1):** 1080x1080 (thumbnails)
