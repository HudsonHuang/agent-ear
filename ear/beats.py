"""Beat/rhythm layer: Beat This! (default) with a librosa fallback."""
from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

import numpy as np


class BeatError(RuntimeError):
    pass


def available() -> bool:
    try:
        import beat_this  # noqa: F401
        return True
    except Exception:
        return False


def _bpm(beats: np.ndarray) -> float | None:
    if len(beats) < 3:
        return None
    d = np.diff(beats)
    d = d[d > 0.05]
    if len(d) == 0:
        return None
    med = float(statistics.median(d))
    if med <= 0:
        return None
    return round(60.0 / med, 1)


def _positions(beats: np.ndarray, downbeats: np.ndarray) -> tuple[list[int], int | None]:
    if len(beats) == 0:
        return [], None
    if len(downbeats) == 0:
        return [1] * len(beats), None
    positions: list[int] = []
    d_idx = 0
    count = 0
    for b in beats:
        while d_idx + 1 < len(downbeats) and b >= downbeats[d_idx + 1] - 0.03:
            d_idx += 1
            count = 0
        positions.append(count % 8 + 1)
        count += 1
    # Most common bar length (excluding 1-off noise).
    diffs = np.diff(downbeats)
    meter = None
    if len(diffs):
        # beats per bar = median beat index delta between downbeats
        idx = np.searchsorted(beats, downbeats)
        spans = np.diff(idx)
        spans = spans[(spans >= 2) & (spans <= 12)]
        if len(spans):
            meter = int(round(float(np.median(spans))))
    return positions, meter


def track(path: Path, *, device: str = "cpu", model: str = "small0") -> dict[str, Any]:
    """Run Beat This! on a wav file. Falls back to librosa if unavailable."""
    try:
        from .models import ensure_model
        from beat_this.inference import File2Beats
        checkpoint = ensure_model("beat_this_small0") if model == "small0" else None
        f2b = File2Beats(
            checkpoint_path=str(checkpoint) if checkpoint else model,
            device=device, dbn=False)
        beats, downbeats = f2b(str(path))
        beats = np.asarray(beats, dtype=float)
        downbeats = np.asarray(downbeats, dtype=float)
        provider, quality = f"beat_this-{model}", "model"
    except Exception:
        import librosa
        y, sr = librosa.load(str(path), sr=22050, mono=True)
        tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        beats = librosa.frames_to_time(frames, sr=sr)
        downbeats = np.array([], dtype=float)
        provider, quality = "librosa-beat_track", "fallback"
        tempo = float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else None
        return {
            "provider": provider,
            "quality": quality,
            "bpm": round(tempo, 1) if tempo else _bpm(beats),
            "beats_ms": [int(round(b * 1000)) for b in beats],
            "downbeats_ms": [],
            "beat_positions": [1] * len(beats),
            "meter": None,
            "conf": None,
        }

    positions, meter = _positions(beats, downbeats)
    return {
        "provider": provider,
        "quality": quality,
        "bpm": _bpm(beats),
        "beats_ms": [int(round(b * 1000)) for b in beats],
        "downbeats_ms": [int(round(b * 1000)) for b in downbeats],
        "beat_positions": positions,
        "meter": meter,
        "conf": None,
    }
