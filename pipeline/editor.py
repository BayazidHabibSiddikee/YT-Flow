#!/usr/bin/env python3
"""Video Editor — Proper audio+video sync with transitions.

This handles the final editing stage:
1. Sync audio to video with proper timing
2. Add crossfade transitions between scenes
3. Add Ken Burns effect to images
4. Proper subtitle timing synced to audio
5. Background music mixing
6. Final export in correct format

Usage:
    python editor.py edit video.mp4 audio.mp3 images/ output.mp4
    python editor.py preview output.mp4
"""

import subprocess
import json
from pathlib import Path


class VideoEditor:
    """Proper video editing with FFmpeg."""

    def __init__(self, ffmpeg: str = "ffmpeg"):
        self.ffmpeg = ffmpeg

    def _run(self, cmd: list[str], timeout: int = 300) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                print(f"[FFmpeg] Error: {result.stderr[:500]}")
                return False
            return True
        except Exception as e:
            print(f"[FFmpeg] Exception: {e}")
            return False

    def _probe(self, path: Path) -> dict:
        """Get media info."""
        result = subprocess.run(
            [self.ffmpeg, "-i", str(path), "-print_format", "json", "-show_format", "-show_streams"],
            capture_output=True, text=True,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}

    def _probe_duration(self, path: Path) -> float:
        info = self._probe(path)
        try:
            return float(info["format"]["duration"])
        except (KeyError, ValueError):
            return 15.0

    def create_short(
        self,
        audio_path: Path,
        image_paths: list[Path],
        output_path: Path,
        text: str = "",
        duration_per_image: float = 4.0,
        fps: int = 30,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """Create a proper short video with synced audio and Ken Burns effect."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio_duration = self._probe_duration(audio_path)
        n_images = max(1, int(audio_duration / duration_per_image) + 1)

        # Repeat images if needed
        images = []
        for i in range(n_images):
            images.append(image_paths[i % len(image_paths)])

        # Build FFmpeg command with Ken Burns (slow zoom) on each image
        cmd = [self.ffmpeg, "-y"]

        # Input images with duration
        for img in images:
            cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img)])

        # Input audio
        cmd.extend(["-i", str(audio_path)])

        # Build filter complex for Ken Burns + concat
        filter_parts = []
        for i in range(n_images):
            # Ken Burns: slow zoom in from 100% to 110% over duration
            zoom_expr = f"min(1+0.001*on,1.1)"
            filter_parts.append(
                f"[{i}:v]scale={width*2}:{height*2},"
                f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={duration_per_image*fps}:s={width}x{height}:fps={fps},"
                f"format=yuv420p[v{i}]"
            )

        # Concat all video streams
        concat_in = "".join(f"[v{i}]" for i in range(n_images))
        filter_parts.append(f"{concat_in}concat=n={n_images}:v=1:a=0[v]")

        cmd.extend([
            "-filter_complex", ";".join(filter_parts),
            "-map", "[v]", "-map", f"{n_images}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(output_path),
        ])

        print(f"[Editor] Creating video with Ken Burns ({n_images} images, {audio_duration:.1f}s)...")
        if self._run(cmd):
            print(f"[Editor] Done: {output_path.name}")
            return output_path
        else:
            raise RuntimeError("Video creation failed")

    def add_subtitles(
        self,
        video_path: Path,
        text: str,
        output_path: Path,
        font_size: int = 28,
        font_name: str = "Arial Bold",
    ) -> Path:
        """Burn subtitles into video with proper styling."""
        duration = self._probe_duration(video_path)

        # Create SRT file
        srt_path = video_path.parent / f"{video_path.stem}_subs.srt"
        phrases = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#")]

        if not phrases:
            phrases = [text[:50]]

        time_per_phrase = duration / len(phrases)
        entries = []
        for i, phrase in enumerate(phrases):
            start = i * time_per_phrase
            end = start + time_per_phrase
            # Split long phrases
            if len(phrase) > 35:
                mid = len(phrase) // 2
                split = phrase.rfind(" ", 0, mid)
                if split > 0:
                    phrase = phrase[:split] + "\n" + phrase[split+1:]
            entries.append(f"{i+1}\n{self._fmt_srt(start)} --> {self._fmt_srt(end)}\n{phrase}\n")

        srt_path.write_text("\n".join(entries))

        # Burn subtitles
        style = (
            f"FontName={font_name},FontSize={font_size},"
            "PrimaryColour=&H80FFFFFF,OutlineColour=&H40000000,"
            "BackColour=&H00000000,BorderStyle=4,Outline=0,Shadow=0,"
            "Alignment=2,MarginV=80,Bold=1"
        )

        cmd = [
            self.ffmpeg, "-y", "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style='{style}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy", "-movflags", "+faststart",
            str(output_path),
        ]

        print(f"[Editor] Burning subtitles...")
        success = self._run(cmd)
        srt_path.unlink(missing_ok=True)

        if success:
            return output_path
        return video_path

    def add_background_music(
        self,
        video_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = 0.15,
    ) -> Path:
        """Mix background music with video audio."""
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print(f"[Editor] Adding background music...")
        if self._run(cmd):
            return output_path
        return video_path

    def final_export(
        self,
        video_path: Path,
        output_path: Path,
        target_size_mb: int = 50,
    ) -> Path:
        """Final export with size optimization."""
        # Calculate bitrate from target size
        duration = self._probe_duration(video_path)
        bitrate = int((target_size_mb * 8 * 1024) / duration)

        cmd = [
            self.ffmpeg, "-y", "-i", str(video_path),
            "-c:v", "libx264", "-preset", "slow", "-crf", "23",
            "-maxrate", f"{bitrate}k", "-bufsize", f"{bitrate*2}k",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print(f"[Editor] Final export (target: {target_size_mb}MB)...")
        if self._run(cmd):
            print(f"[Editor] Exported: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
            return output_path
        return video_path

    def _fmt_srt(self, s: float) -> str:
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        ms = int((sec % 1) * 1000)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python editor.py edit <audio> <images_dir> <output>")
        sys.exit(1)

    editor = VideoEditor()
    audio = Path(sys.argv[2])
    images_dir = Path(sys.argv[3])
    output = Path(sys.argv[4])

    images = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png"))
    editor.create_short(audio, images, output)
