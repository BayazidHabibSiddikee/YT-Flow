#!/usr/bin/env python3
"""
YT-Flow: Video Processor
==========================
Extend duration, generate subtitles, burn into video.

Usage:
    python3 scripts/process_video.py --input path/to/video.mp4 --extend-to 22
"""
import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def extend_video(video_path, output_path, target=22):
    dur = get_duration(video_path)
    loops = max(1, int(target / dur) + 1)
    subprocess.run(
        ["ffmpeg", "-y", "-stream_loop", str(loops), "-i", video_path,
         "-c", "copy", "-shortest", "-avoid_negative_ts", "make_zero",
         "-t", str(target), output_path],
        check=True,
    )


def burn_subtitles(video_in, video_out, lines):
    """Burn styled subtitles. lines = [(start_sec, end_sec, text), ...]"""
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
        "OutlineColour=&H00000000,Outline=3,Shadow=0,Bold=1,"
        "Alignment=2,MarginV=40'"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_in, "-vf", vf, "-c:a", "copy", video_out],
        check=True,
    )
    os.remove(srt_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YT-Flow video processor")
    parser.add_argument("--input", required=True)
    parser.add_argument("--extend-to", type=int, default=22)
    parser.add_argument("--subtitle-lines", nargs="+", help="Subtitle text lines")
    parser.add_argument("--output")
    args = parser.parse_args()

    raw_name = os.path.splitext(os.path.basename(args.input))[0]
    edited_dir = os.path.join(PROJECT_DIR, "videos", "edited")
    os.makedirs(edited_dir, exist_ok=True)

    extended = os.path.join(edited_dir, f"{raw_name}_extended.mp4")
    final = args.output or os.path.join(edited_dir, f"{raw_name}_final.mp4")

    print(f"📹 Processing: {args.input}")
    extend_video(args.input, extended, args.extend_to)
    print(f"   Extended: {get_duration(extended):.1f}s")

    if args.subtitle_lines:
        lines = []
        dur = get_duration(extended)
        chunk = dur / len(args.subtitle_lines)
        for i, txt in enumerate(args.subtitle_lines):
            lines.append((i * chunk + 0.5, (i + 1) * chunk, txt))
        burn_subtitles(extended, final, lines)
        os.remove(extended)
    else:
        os.rename(extended, final)

    print(f"✅ Done: {final} ({get_duration(final):.1f}s)")
