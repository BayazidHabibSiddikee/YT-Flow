# Image Slideshow Video Pipeline

A simple pipeline to create videos from images with text overlays and audio.

## Quick Start

```bash
# Add your images to the images folder
mkdir -p ~/Documents/video_gen/images
cp /path/to/your/images/*.jpg ~/Documents/video_gen/images/

# Generate video
python ~/Documents/video_gen/slideshow.py --topic "My Video" --interval 3

# With text overlay
python ~/Documents/video_gen/slideshow.py --topic "Tutorial" --text "Welcome to the tutorial"
```

## Usage

```
python slideshow.py [OPTIONS]

Options:
  --images PATH    Folder containing images (default: ~/Documents/video_gen/images)
  --output PATH    Output folder (default: ~/Documents/video_gen/downloads)
  --topic TEXT     Video title/topic (default: "Slideshow")
  --interval INT   Seconds per image (default: 3)
  --text TEXT      Text overlay (JSON or plain text)
  --fps INT        Frames per second (default: 24)
  --help           Show this message
```

## Examples

### Basic slideshow
```bash
python slideshow.py --topic "Vacation Photos" --interval 4
```

### With text
```bash
python slideshow.py --topic "Tutorial" --text "Step 1: Open the app"
```

### Custom folder
```bash
python slideshow.py --images ~/Downloads/photos --interval 2
```

## Output

- Videos: `downloads/TOPIC_slideshow.mp4` (video only)
- Final: `downloads/TOPIC_final.mp4` (video + audio)
- Audio: `downloads/TOPIC_audio.wav` (raw audio track)

## Requirements

- Python 3.8+
- ffmpeg installed
- PIL/Pillow for image processing
- No API keys required!

## Limitations

- Simple slideshow (no transitions)
- Basic text overlay
- Silent audio track (no voice)
- 1920x1080 output resolution

## Future Enhancements

- [ ] Add transitions between slides
- [ ] Add voice narration
- [ ] Support custom fonts
- [ ] Add background music
- [ ] Create thumbnail generation
