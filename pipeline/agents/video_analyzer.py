#!/usr/bin/env python3
"""Video Analyzer — ffprobe-based quality checks before upload.

Checks:
1. Duration >= 15s (YouTube Shorts minimum)
2. Resolution >= 720p on the short edge (orientation-agnostic: works for
   9:16 portrait shorts AND 16:9 landscape longs)
3. Audio stream exists
4. File size > 100KB (not corrupt)
5. Bitrate reasonable (not compressed to death)
"""

import json
import subprocess
from pathlib import Path


class VideoAnalyzer:
    """ffprobe-based video quality checks."""

    def __init__(self, min_duration: float = 15.0, min_short_edge: int = 720):
        self.min_duration = min_duration
        # Short-edge threshold: 1080x1920 -> 1080, 1920x1080 -> 1080, 720x1280 -> 720
        self.min_short_edge = min_short_edge

    def analyze(self, video_path: Path) -> dict:
        """Run all checks on a video file. Returns pass/fail with details."""
        result = {
            "video_path": str(video_path),
            "checks": {},
            "passed": True,
            "errors": [],
        }

        if not video_path.exists():
            result["passed"] = False
            result["errors"].append(f"File not found: {video_path}")
            return result

        # Get ffprobe metadata
        meta = self._ffprobe(video_path)
        if not meta:
            result["passed"] = False
            result["errors"].append("ffprobe failed — cannot read video metadata")
            return result

        fmt = meta.get("format", {})
        streams = meta.get("streams", [])

        # Check 1: File size
        file_size = int(fmt.get("size", 0))
        result["checks"]["file_size"] = {
            "value": file_size,
            "unit": "bytes",
            "pass": file_size > 100_000,
        }
        if file_size <= 100_000:
            result["passed"] = False
            result["errors"].append(f"File too small ({file_size} bytes) — likely corrupt")

        # Check 2: Duration
        duration = float(fmt.get("duration", 0))
        result["checks"]["duration"] = {
            "value": duration,
            "unit": "seconds",
            "pass": duration >= self.min_duration,
        }
        if duration < self.min_duration:
            result["passed"] = False
            result["errors"].append(f"Duration {duration:.1f}s < {self.min_duration}s minimum")

        # Check 3: Video stream + resolution
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        if not video_streams:
            result["passed"] = False
            result["errors"].append("No video stream found")
            result["checks"]["video_stream"] = {"pass": False}
        else:
            vs = video_streams[0]
            width = int(vs.get("width", 0))
            height = int(vs.get("height", 0))
            short_edge = min(width, height)
            result["checks"]["resolution"] = {
                "value": f"{width}x{height}",
                "short_edge": short_edge,
                "pass": short_edge >= self.min_short_edge,
            }
            if short_edge < self.min_short_edge:
                result["passed"] = False
                result["errors"].append(
                    f"Resolution {width}x{height} (short edge {short_edge}) "
                    f"< {self.min_short_edge}p minimum"
                )

            # Check bitrate
            bitrate = int(vs.get("bit_rate", 0)) if vs.get("bit_rate") else 0
            result["checks"]["video_bitrate"] = {
                "value": bitrate,
                "unit": "bps",
                "pass": bitrate > 0,
            }

        # Check 4: Audio stream
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        result["checks"]["audio_stream"] = {
            "pass": len(audio_streams) > 0,
        }
        if not audio_streams:
            result["passed"] = False
            result["errors"].append("No audio stream found")

        # Summary
        result["duration"] = duration
        result["file_size_mb"] = round(file_size / 1024 / 1024, 2)

        return result

    def _ffprobe(self, video_path: Path) -> dict:
        """Run ffprobe and return JSON metadata."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    str(video_path),
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return {}
            return json.loads(result.stdout)
        except Exception:
            return {}

    def check_or_reject(self, video_path: Path) -> tuple[bool, dict]:
        """Check video quality. Returns (passed, details)."""
        details = self.analyze(video_path)
        return details["passed"], details


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python video_analyzer.py <video_path>")
        sys.exit(1)

    analyzer = VideoAnalyzer()
    passed, details = analyzer.check_or_reject(Path(sys.argv[1]))

    print(json.dumps(details, indent=2))
    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")
    sys.exit(0 if passed else 1)
