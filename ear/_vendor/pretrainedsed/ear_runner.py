"""Frame-level AED runner for PretrainedSED BEATs Strong.

Standalone subprocess entry point: keeps heavy imports and checkpoint loading
out of the main ear process.  Outputs JSON events on a 40 ms grid.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

# Make the vendored PretrainedSED modules importable as top-level packages.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402

GENERIC = {
    "Speech", "Music", "Silence", "Inside, small room", "Background noise",
    "Human voice", "Conversation", "Narration, monologue",
    "Female speech, woman speaking", "Male speech, man speaking",
    "Child speech, kid speaking", "Speech synthesizer",
}


def _runs(mask: np.ndarray, *, min_len: int, max_gap: int) -> list[tuple[int, int]]:
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    out: list[tuple[int, int]] = []
    start = prev = int(idx[0])
    for raw in idx[1:]:
        i = int(raw)
        if i - prev <= max_gap + 1:
            prev = i
            continue
        if prev - start + 1 >= min_len:
            out.append((start, prev))
        start = prev = i
    if prev - start + 1 >= min_len:
        out.append((start, prev))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threshold", type=float, default=0.35)
    ap.add_argument("--median-frames", type=int, default=7)
    ap.add_argument("--min-ms", type=int, default=100)
    args = ap.parse_args()

    import librosa
    import torch
    from scipy.ndimage import median_filter

    # Must be set before models.prediction_wrapper reads RESOURCES_FOLDER.
    config.RESOURCES_FOLDER = str(Path(args.checkpoint).parent)
    from data_util.audioset_classes import as_strong_train_classes
    from models.beats.BEATs_wrapper import BEATsWrapper
    from models.prediction_wrapper import PredictionsWrapper

    t0 = time.time()
    beats = BEATsWrapper()
    model = PredictionsWrapper(beats, checkpoint="BEATs_strong_1")
    model.eval()
    model.to(args.device)

    audio, _ = librosa.load(args.audio, sr=16000, mono=True)
    duration_ms = int(round(len(audio) / 16000 * 1000))
    seg = 16000 * 10
    chunks = []
    for i in range(0, len(audio), seg):
        ch = audio[i:i + seg]
        if len(ch) < seg:
            ch = np.pad(ch, (0, seg - len(ch)))
        x = torch.from_numpy(ch[None, :]).float().to(args.device)
        with torch.no_grad():
            mel = model.mel_forward(x)
            y, _ = model(mel)
        chunks.append(y)
    y = torch.cat(chunks, dim=2).sigmoid().cpu().numpy()[0]  # (447, T)
    n_classes, n_frames = y.shape
    frame_ms = 40.0
    infer_s = time.time() - t0

    class_names = list(as_strong_train_classes)
    events: list[dict] = []
    top = []
    for j, label in enumerate(class_names):
        row = y[j]
        peak = float(row.max())
        top.append((label, peak))
        if label in GENERIC:
            continue
        smooth = median_filter(row, size=args.median_frames, mode="nearest")
        min_len = max(1, int(round(args.min_ms / frame_ms)))
        max_gap = max(0, int(round(120 / frame_ms)))
        for a, b in _runs(smooth >= args.threshold, min_len=min_len, max_gap=max_gap):
            start_ms = int(round(a * frame_ms))
            end_ms = min(duration_ms, int(round((b + 1) * frame_ms)))
            if end_ms <= start_ms:
                continue
            events.append({
                "start_ms": start_ms,
                "end_ms": end_ms,
                "label": label,
                "conf": round(float(np.mean(row[a:b + 1])), 3),
                "salience": round(peak, 3),
                "source": "pretrainedsed-beats-strong",
            })
    events.sort(key=lambda e: (e["start_ms"], -e["salience"]))
    for i, e in enumerate(events, 1):
        e["id"] = f"ev_{i:04d}"

    top.sort(key=lambda x: x[1], reverse=True)
    def ratio(names: set[str], thr: float = 0.5) -> float:
        idx = [i for i, n in enumerate(class_names) if n in names]
        if not idx:
            return 0.0
        return float(np.mean(np.max(y[idx], axis=0) >= thr))
    speech_ratio = ratio({"Speech", "Female speech, woman speaking",
                          "Male speech, man speaking", "Child speech, kid speaking"})
    music_ratio = ratio({"Music"}, 0.3)
    event_ratio = 0.0
    event_idx = [i for i, n in enumerate(class_names) if n not in GENERIC]
    if event_idx:
        event_ratio = float(np.mean(np.max(y[event_idx], axis=0) >= args.threshold))

    payload = {
        "provider": "pretrainedsed-beats-strong",
        "model": "BEATs_strong_1",
        "frame_ms": frame_ms,
        "classes": n_classes,
        "duration_ms": duration_ms,
        "inference_seconds": round(infer_s, 2),
        "speech_ratio": round(speech_ratio, 4),
        "music_ratio": round(music_ratio, 4),
        "event_ratio": round(event_ratio, 4),
        "top_labels": [{"label": k, "score": round(v, 4)} for k, v in top[:12]],
        "events": events,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
