#!/usr/bin/env python3
"""Process video: extend duration, generate subtitles, burn in."""
import subprocess
import os
import sys

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())

def extend_video(video_path, output_path, target=22):
    dur = get_duration(video_path)
    loops = max(1, int(target / dur) + 1)
    subprocess.run(
        ["ffmpeg", "-y", "-stream_loop", str(loops), "-i", video_path,
         "-c", "copy", "-shortest", "-avoid_negative_ts", "make_zero",
         "-t", str(target), output_path],
        check=True
    )

def burn_subtitles(video_in, video_out, lines):
    srt = ""
    for i, (s, e, txt) in enumerate(lines, 1):
        sh, sm = int(s // 3600), int((s % 3600) // 60)
        ss = int(s % 60)
        eh, em = int(e // 3600), int((e % 3600) // 60)
        es = int(e % 60)
        srt += f"{i}\n{sh:02d}:{sm:02d}:{ss:02d},000 --> {eh:02d}:{em:02d}:{es:02d},000\n{txt}\n\n"
    srt_path = "/tmp/ytflow_subs.srt"
    with open(srt_path, "w") as f:
        f.write(srt)
    vf = (
        f"subtitles={srt_path}:force_style='"
        "FontName=Arial Black,FontSize=32,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=3,Shadow=0,Bold=1,Alignment=2,MarginV=40'"
    )
    subprocess.run(["ffmpeg", "-y", "-i", video_in, "-vf", vf, "-c:a", "copy", video_out], check=True)
    os.remove(srt_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YT-Flow video processor")
    parser.add_argument("--input", required=True)
    parser.add_argument("--extend-to", type=int, default=22)
    parser.add_argument("--subtitle-file", help="SRT file to burn in")
    parser.add_argument("--output", help="Output path")
    args = parser.parse_args()

    raw_name = os.path.splitext(os.path.basename(args.input))[0]
    edited_dir = os.path.join(os.path.dirname(__file__), "..", "videos", "edited")
    os.makedirs(edited_dir, exist_ok=True)

    extended = os.path.join(edited_dir, f"{raw_name}_extended.mp4")
    final = args.output or os.path.join(edited_dir, f"{raw_name}_final.mp4")

    print(f"Processing: {args.input}")
    extend_video(args.input, extended, args.extend_to)
    if args.subtitle_file:
        # Parse SRT and burn
        burn_subtitles(extended, final, [])  # placeholder - use provided SRT
    else:
        os.rename(extended, final)
    print(f"✅ Done: {final} ({get_duration(final):.1f}s)")
