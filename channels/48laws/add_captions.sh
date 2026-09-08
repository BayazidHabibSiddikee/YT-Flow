#!/bin/bash
# Add captions to law videos with Piper audio
set -e

VIDEO_DIR="/home/sword/Documents/48laws-pipeline/output"

# law_01 - short video
echo "Processing law_01..."
ffmpeg -y -i "${VIDEO_DIR}/law_01_piper.mp4" \
    -vf "drawtext=text='Law 1: Never Outshine the Master':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-80:start=0:end=5.033" \
    -c:a copy "${VIDEO_DIR}/law_01_captions.mp4" 2>&1 | tail -3
echo "Done"

# law_2
echo "Processing law_2..."
ffmpeg -y -i "${VIDEO_DIR}/law_2_piper.mp4" \
    -vf "drawtext=text='Law 2: Never Put Too Much Trust in Friends':fontsize=44:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-120:start=0:end=5.0,drawtext=text='Learn How to Use Enemies':fontsize=44:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-80:start=5.0:end=10.0,drawtext=text='Friends betray out of envy. Enemies betray out of necessity.':fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-80:start=10.0:end=14.97" \
    -c:a copy "${VIDEO_DIR}/law_2_captions.mp4" 2>&1 | tail -3
echo "Done"

# law_3
echo "Processing law_3..."
ffmpeg -y -i "${VIDEO_DIR}/law_3_piper.mp4" \
    -vf "drawtext=text='Law 3: Conceal Your Intentions':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-120:start=0:end=5.0,drawtext=text='Keep people off-balance by never revealing the purpose behind your actions.':fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-80:start=5.0:end=10.0,drawtext=text='The most powerful person is the one no one sees coming.':fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-text_h-80:start=10.0:end=14.97" \
    -c:a copy "${VIDEO_DIR}/law_3_captions.mp4" 2>&1 | tail -3
echo "Done"

echo ""
echo "=== All videos with captions ==="
ls -lh "${VIDEO_DIR}"/*_captions.mp4
