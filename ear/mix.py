"""Cheap local mix inspection for editors and DAW feedback loops."""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from . import media


def _db(x: float) -> float | None:
    return round(20.0 * math.log10(max(x, 1e-12)), 2)


def analyze(src: Path) -> dict[str, Any]:
    info = media.media_info(src)
    if not info.get("has_audio"):
        raise ValueError("no audio stream")
    loud = media.loudness(src)
    with tempfile.TemporaryDirectory(prefix="agent-ear-mix-") as td:
        wav = media.extract_audio(src, Path(td) / "a.wav", sr=16000)
        import soundfile as sf
        y, sr = sf.read(str(wav), dtype="float32", always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if len(y) == 0:
        raise ValueError("empty audio")
    y = np.asarray(y, dtype=np.float64)
    peak = float(np.max(np.abs(y)))
    rms = float(np.sqrt(np.mean(y * y)))
    clip_n = int(np.count_nonzero(np.abs(y) >= 0.999))
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y)))) ** 2
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    total = float(np.sum(spec)) or 1.0

    def band(lo: float, hi: float) -> dict[str, float]:
        m = (freqs >= lo) & (freqs < hi)
        p = float(np.sum(spec[m]))
        return {"pct": round(p / total * 100, 2), "db": round(10 * math.log10(max(p, 1e-12) / total), 2)}

    return {
        "path": str(src),
        "duration_s": round(len(y) / sr, 3),
        "sample_rate": sr,
        "lufs": loud.get("integrated_lufs"),
        "true_peak_db": loud.get("true_peak_db"),
        "lra": loud.get("lra"),
        "peak_dbfs": _db(peak),
        "rms_dbfs": _db(rms),
        "crest_db": round((_db(peak) if _db(peak) is not None else -120)
                          - (_db(rms) if _db(rms) is not None else -120), 2),
        "clipping_samples": clip_n,
        "clipping_ratio": round(clip_n / len(y), 6),
        "bands_pct": {"low": band(20, 250), "mid": band(250, 2000),
                      "high_mid": band(2000, 8000), "high": band(8000, 20000)},
        "warnings": ([] if clip_n == 0 else [f"clipping: {clip_n} samples at/above 0 dBFS"]),
    }


def compare(a: Path, b: Path) -> dict[str, Any]:
    x, y = analyze(a), analyze(b)
    keys = ["lufs", "true_peak_db", "lra", "peak_dbfs", "rms_dbfs", "crest_db"]
    delta = {}
    for k in keys:
        if isinstance(x.get(k), (int, float)) and isinstance(y.get(k), (int, float)):
            delta[k] = round(y[k] - x[k], 2)
    return {"a": x, "b": y, "delta_b_minus_a": delta,
            "warnings": x.get("warnings", []) + y.get("warnings", [])}
