# Video Generation Pipeline

## Status: WORKING (with caveats)

### What Works
- ✅ Video generation (fallback slideshow mode)
- ✅ Audio generation (espeak TTS)
- ✅ Video + audio merging
- ✅ fal.ai API integration (attempted, but account needs funding)

### What's Blocked
- ❌ fal.ai video generation: Account locked (TOP_UP required)
  - Visit: https://fal.ai/dashboard
  - Add payment method and credits
  - After funding, API will work automatically

### Files
- `pipeline.py` - Main pipeline script
- `config.env.example` - Environment template
- `.env` - Your active configuration (FAL_KEY configured)
- `downloads/` - Output directory

### Usage
```bash
cd ~/Documents/video_gen
source venv/bin/activate

# Generate with fal.ai (requires funded account)
python pipeline.py --topic "Your Topic" --duration 60

# Generate with fallback slideshow
python pipeline.py --topic "Your Topic" --duration 60 --no-fal

# With VibeVoice (requires GPU)
python pipeline.py --topic "Your Topic" --duration 60 --vibevoice
```

### Output
- Video: `downloads/{topic}_final.mp4`
- Audio: `downloads/{topic}_audio.wav`

### Next Steps for Full Automation
1. Fund fal.ai account (add payment method)
2. Provide social media API keys:
   - YouTube API key
   - Facebook Page token
   - Instagram access token
   - TikTok access token (requires approval)
3. Set up OAuth for YouTube (for upload)
4. Configure social media posting
