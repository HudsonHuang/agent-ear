"""Probe: cheap signal-level facts before spending on models."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import media


def _speech_silero(wav_path: Path) -> tuple[list[dict[str, int]], float] | None:
    try:
        import numpy as np
        import soundfile as sf
        import torch
        from silero_vad import get_speech_timestamps, load_silero_vad
    except Exception as exc:  # pragma: no cover - optional dependency
        return None

    data, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        # caller extracts 16k; guard anyway
        return None
    tensor = torch.from_numpy(np.ascontiguousarray(data))
    model = load_silero_vad()
    try:
        spans = get_speech_timestamps(
            tensor, model, sampling_rate=16000, return_seconds=False,
            min_speech_duration_ms=200, min_silence_duration_ms=300,
            speech_pad_ms=60,
        )
    except Exception:
        return None
    out = [
        {"start_ms": int(s["start"] * 1000 / 16000), "end_ms": int(s["end"] * 1000 / 16000)}
        for s in spans
    ]
    total = float(data.shape[0]) / 16000.0
    speech = sum((s["end_ms"] - s["start_ms"]) for s in out) / 1000.0
    ratio = min(1.0, speech / total) if total > 0 else 0.0
    return out, round(ratio, 4)


def probe_audio(src: Path, workdir: Path) -> dict[str, Any]:
    workdir.mkdir(parents=True, exist_ok=True)
    info = media.media_info(src)
    warnings: list[str] = []
    capabilities: dict[str, Any] = {}

    if not info["has_audio"]:
        return {
            "media": info,
            "duration_ms": info["duration_ms"],
            "has_audio": False,
            "speech": {"ratio": 0.0, "segments": [], "method": None},
            "silence": [],
            "loudness": {"available": False},
            "warnings": ["no audio stream"],
            "capabilities": capabilities,
        }

    wav = workdir / "audio_16k.wav"
    if not wav.is_file():
        media.extract_audio(src, wav)

    duration_ms = info["duration_ms"] or int(round(_wav_duration(wav) * 1000))
    loud = media.loudness(wav)
    silence = media.silences(wav)

    speech = _speech_silero(wav)
    if speech is None:
        warnings.append("silero-vad unavailable; speech ratio falls back to silence map")
        capabilities["vad"] = "silence-fallback"
        silent_ms = sum(s["end_ms"] - s["start_ms"] for s in silence)
        ratio = max(0.0, 1.0 - silent_ms / duration_ms) if duration_ms else 0.0
        speech_segments: list[dict[str, int]] = []
        speech_ratio = round(ratio, 4)
    else:
        speech_segments, speech_ratio = speech
        capabilities["vad"] = "silero-vad"

    return {
        "media": info,
        "duration_ms": duration_ms,
        "has_audio": True,
        "loudness": loud,
        "silence": silence,
        "speech": {
            "ratio": speech_ratio,
            "segments": speech_segments,
            "method": capabilities.get("vad"),
        },
        "warnings": warnings,
        "capabilities": capabilities,
    }


def _wav_duration(path: Path) -> float:
    try:
        import soundfile as sf
        return float(sf.info(str(path)).duration)
    except Exception:
        return 0.0
