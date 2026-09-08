#!/usr/bin/env python3
"""Pipeline Video Combiner — FFmpeg

Always burns subtitles into video.
Creates vertical (9:16) shorts and horizontal (16:9) longs.
"""

import subprocess
from pathlib import Path

from config import FFMPEG_PATH, VIDEO_RESOLUTION


class VideoCombiner:
    """FFmpeg video creation with mandatory subtitles."""

    def __init__(self):
        self.ffmpeg = FFMPEG_PATH
        self.width, self.height = VIDEO_RESOLUTION

    def _run(self, cmd: list[str], timeout: int = 600) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                print(f"[FFmpeg] Error: {result.stderr[:400]}")
                return False
            return True
        except Exception as e:
            print(f"[FFmpeg] Exception: {e}")
            return False

    def _probe_duration(self, path: Path) -> float:
        result = subprocess.run(
            [self.ffmpeg, "-i", str(path), "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True,
        )
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 30.0

    def _text_to_srt(self, text: str, srt_path: Path, audio_duration: float = 15.0):
        """Convert text to SRT synced with audio duration."""
        # Split into natural phrases (sentences or line breaks)
        phrases = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Split long lines into shorter phrases
                if len(line) > 40:
                    parts = line.split(", ")
                    phrases.extend([p.strip() for p in parts if p.strip()])
                else:
                    phrases.append(line)

        if not phrases:
            phrases = [text[:50]]

        # Distribute timing evenly across audio duration
        time_per_phrase = audio_duration / len(phrases)

        entries = []
        for i, phrase in enumerate(phrases):
            start = i * time_per_phrase
            end = start + time_per_phrase
            entries.append(f"{i+1}\n{self._fmt_srt(start)} --> {self._fmt_srt(end)}\n{phrase}\n")

        srt_path.parent.mkdir(parents=True, exist_ok=True)
        srt_path.write_text("\n".join(entries))

        srt_path.parent.mkdir(parents=True, exist_ok=True)
        srt_path.write_text("\n".join(entries))

    def _fmt_srt(self, s: float) -> str:
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        ms = int((sec % 1) * 1000)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"

    def _burn_subtitles(self, video_path: Path, text: str, output_path: Path) -> Path:
        """Burn subtitles into video — always called."""
        # Get video duration for subtitle timing
        duration = self._probe_duration(video_path)
        srt_path = video_path.parent / f"{video_path.stem}_subs.srt"
        self._text_to_srt(text, srt_path, audio_duration=duration)

        # Style: minimal clean subtitles
        style = (
            "FontName=Arial,FontSize=12,PrimaryColour=&H80FFFFFF,"
            "OutlineColour=&H40000000,BackColour=&H00000000,"
            "BorderStyle=4,Outline=0,Shadow=0,"
            "Alignment=2,MarginV=40,Bold=0"
        )

        cmd = [
            self.ffmpeg, "-y", "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style='{style}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print(f"[FFmpeg] Burning subtitles...")
        success = self._run(cmd)
        srt_path.unlink(missing_ok=True)
        if success:
            return output_path
        return video_path

    def images_audio_to_video(
        self,
        audio_path: Path,
        image_paths: list[Path],
        output_path: Path,
        text: str = "",
        duration_per_image: float = 4.0,
    ) -> Path:
        """Create video from images + audio with subtitles always burned in."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio_duration = self._probe_duration(audio_path)

        # Repeat images if needed
        total_img_time = len(image_paths) * duration_per_image
        if total_img_time < audio_duration:
            repeats = int(audio_duration / total_img_time) + 1
            image_paths = image_paths * repeats

        n_images = min(len(image_paths), int(audio_duration / duration_per_image) + 1)

        # Step 1: Create video from images + audio (no subs yet)
        temp_video = output_path.parent / f"temp_{output_path.name}"

        cmd = [self.ffmpeg, "-y"]
        for img in image_paths[:n_images]:
            cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img)])
        cmd.extend(["-i", str(audio_path)])

        filter_parts = []
        for i in range(n_images):
            filter_parts.append(
                f"[{i}:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v{i}]"
            )
        concat_in = "".join(f"[v{i}]" for i in range(n_images))
        filter_parts.append(f"{concat_in}concat=n={n_images}:v=1:a=0[v]")

        cmd.extend([
            "-filter_complex", ";".join(filter_parts),
            "-map", "[v]", "-map", f"{n_images}:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(temp_video),
        ])

        print(f"[FFmpeg] Creating base video ({n_images} images)...")
        if not self._run(cmd):
            raise RuntimeError("Base video creation failed")

        # Step 2: Always burn subtitles
        if text:
            final = self._burn_subtitles(temp_video, text, output_path)
            temp_video.unlink(missing_ok=True)
            print(f"[FFmpeg] Done with subtitles: {output_path.name}")
            return final
        else:
            temp_video.rename(output_path)
            print(f"[FFmpeg] Done (no text for subs): {output_path.name}")
            return output_path

    def merge_audio_video(
        self, video_path: Path, audio_path: Path, output_path: Path, text: str = ""
    ) -> Path:
        """Merge audio + video with subtitles."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp = output_path.parent / f"temp_{output_path.name}"
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(video_path), "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            "-movflags", "+faststart", str(temp),
        ]

        print(f"[FFmpeg] Merging audio...")
        if not self._run(cmd):
            raise RuntimeError("Merge failed")

        if text:
            final = self._burn_subtitles(temp, text, output_path)
            temp.unlink(missing_ok=True)
            return final
        else:
            temp.rename(output_path)
            return output_path
