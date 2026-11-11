"""Media utilities: ffprobe/ffmpeg wrappers, hashing, probing."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


class MediaError(RuntimeError):
    pass


def run(cmd: list[str], *, timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def ffprobe_json(path: Path) -> dict[str, Any]:
    p = run([FFPROBE, "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)], timeout=120)
    if p.returncode != 0:
        raise MediaError(f"ffprobe failed: {p.stderr[-800:]}")
    return json.loads(p.stdout)


def media_info(path: Path) -> dict[str, Any]:
    data = ffprobe_json(path)
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    duration = float(fmt.get("duration") or 0.0)
    fps = None
    if video and video.get("r_frame_rate"):
        try:
            num, den = video["r_frame_rate"].split("/")
            fps = round(float(num) / float(den), 3) if float(den) else None
        except Exception:
            fps = None
    return {
        "path": str(path),
        "duration_ms": int(round(duration * 1000)),
        "size_bytes": int(fmt.get("size") or path.stat().st_size),
        "format_name": fmt.get("format_name"),
        "bit_rate": int(fmt.get("bit_rate") or 0) or None,
        "has_audio": audio is not None,
        "has_video": video is not None,
        "audio": {
            "codec": (audio or {}).get("codec_name"),
            "sample_rate": int((audio or {}).get("sample_rate") or 0) or None,
            "channels": int((audio or {}).get("channels") or 0) or None,
        } if audio else None,
        "video": {
            "codec": (video or {}).get("codec_name"),
            "width": (video or {}).get("width"),
            "height": (video or {}).get("height"),
            "fps": fps,
        } if video else None,
    }


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def extract_audio(src: Path, dst: Path, *, sr: int = 16000, mono: bool = True) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-y", "-v", "error", "-i", str(src), "-vn",
           "-ac", "1" if mono else "2", "-ar", str(sr), "-c:a", "pcm_s16le", str(dst)]
    p = run(cmd, timeout=3600)
    if p.returncode != 0 or not dst.is_file():
        raise MediaError(f"audio extraction failed: {p.stderr[-800:]}")
    return dst


def cut_audio(src: Path, dst: Path, start_s: float, end_s: float, *, sr: int = 16000) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dur = max(0.05, end_s - start_s)
    cmd = [FFMPEG, "-y", "-v", "error", "-ss", f"{start_s:.3f}", "-i", str(src),
           "-t", f"{dur:.3f}", "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", str(dst)]
    p = run(cmd, timeout=600)
    if p.returncode != 0 or not dst.is_file():
        raise MediaError(f"audio cut failed: {p.stderr[-800:]}")
    return dst


def loudness(path: Path) -> dict[str, Any]:
    """EBU R128 via ffmpeg loudnorm (measurement pass)."""
    cmd = [FFMPEG, "-v", "info", "-i", str(path), "-af",
           "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]
    p = run(cmd, timeout=600)
    text = p.stderr or ""
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", text, flags=re.S)
    if not m:
        return {"available": False}
    try:
        data = json.loads(m[-1])
    except Exception:
        return {"available": False}
    def f(k):
        try:
            return float(data.get(k))
        except Exception:
            return None
    return {
        "available": True,
        "integrated_lufs": f("input_i"),
        "true_peak_db": f("input_tp"),
        "lra": f("input_lra"),
        "threshold": f("input_thresh"),
    }


def silences(path: Path, *, noise_db: float = -35.0, min_s: float = 0.5) -> list[dict[str, int]]:
    cmd = [FFMPEG, "-v", "info", "-i", str(path), "-af",
           f"silencedetect=noise={noise_db}dB:d={min_s}", "-f", "null", "-"]
    p = run(cmd, timeout=600)
    text = p.stderr or ""
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", text)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", text)]
    out = []
    for s, e in zip(starts, ends):
        if e > s:
            out.append({"start_ms": int(round(s * 1000)), "end_ms": int(round(e * 1000))})
    return out


def fmt_ts(ms: int | float, *, always_hours: bool = False) -> str:
    total = max(0.0, float(ms) / 1000.0)
    h = int(total // 3600)
    m = int((total % 3600) // 60)
    s = total % 60
    if h or always_hours:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"
