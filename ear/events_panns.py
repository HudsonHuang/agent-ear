"""PANNs CNN14 sound-event detection + AudioSet tagging.

Default local AED. Frame-level scores are post-processed into intervals.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

# A small Chinese display map; unknown labels fall back to the English key.
ZH = {
    "Laughter": "笑声", "Applause": "掌声", "Speech": "说话", "Music": "音乐",
    "Singing": "唱歌", "Silence": "静音", "Crying, sobbing": "哭声",
    "Sigh": "叹气", "Cough": "咳嗽", "Sneeze": "喷嚏", "Breathing": "呼吸",
    "Footsteps": "脚步声", "Door": "门声", "Knock": "敲门", "Glass": "玻璃声",
    "Shatter": "碎裂", "Whoosh, swoosh, swish": "呼啸/挥动声",
    "Explosion": "爆炸", "Gunshot, gunfire": "枪声", "Siren": "警笛",
    "Alarm": "警报", "Beep, bleep": "提示音", "Buzzer": "蜂鸣",
    "Typing": "打字声", "Keyboard (musical)": "键盘乐器", "Clicking": "点击声",
    "Camera": "相机声", "Static": "静电噪声", "Hum": "嗡鸣", "Noise": "噪声",
    "Thunder": "雷声", "Rain": "雨声", "Wind": "风声", "Water": "水声",
    "Dog": "狗叫", "Cat": "猫叫", "Bird": "鸟叫", "Vehicle": "车辆",
    "Traffic noise, roadway noise": "交通噪声", "Engine": "引擎",
    "Piano": "钢琴", "Guitar": "吉他", "Drum": "鼓", "Bass guitar": "贝斯",
    "Electronic music": "电子音乐", "Pop music": "流行音乐",
    "Rock music": "摇滚", "Hip hop music": "嘻哈",
    "Classical music": "古典音乐", "Jazz": "爵士",
}

EXCLUDE_EVENTS = {"Speech", "Music", "Silence"}


class PannsError(RuntimeError):
    pass


def available() -> bool:
    try:
        import panns_inference  # noqa: F401
        return True
    except Exception:
        return False


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


class PannsTagger:
    """PANNs CNN14 clip-level tagger, applied over sliding windows.

    The frame-level DecisionLevelMax checkpoint is larger and harder to
    download reliably; clip-level CNN14 with 10s/5s windows is the MVP
    compromise.  Each event interval is therefore quantized to the hop.
    """

    WINDOW_S = 10.0
    HOP_S = 5.0

    def __init__(self, device: str = "cpu"):
        try:
            from .models import ensure_model, ensure_panns_labels
            ensure_panns_labels()
            checkpoint = ensure_model("panns_clip")
            from panns_inference import AudioTagging, labels
        except Exception as exc:  # pragma: no cover - optional
            raise PannsError(f"panns_inference/model unavailable: {exc}") from exc
        self.labels = list(labels)
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.at = AudioTagging(checkpoint_path=str(checkpoint), device=device)
        self.device = device

    def analyze(self, wav32k: Path, duration_ms: int, *,
                threshold: float = 0.35, min_event_ms: int = 300,
                max_classes: int = 18) -> dict[str, Any]:
        import librosa

        audio, sr = librosa.load(str(wav32k), sr=32000, mono=True)
        if audio.size == 0:
            raise PannsError("empty audio")
        win = int(self.WINDOW_S * sr)
        hop = int(self.HOP_S * sr)
        if audio.size <= win:
            starts = [0]
        else:
            starts = list(range(0, audio.size - win + 1, hop))
            if starts[-1] + win < audio.size:
                starts.append(audio.size - win)
        scores = []
        for st in starts:
            chunk = audio[st:st + win]
            if chunk.size < win:
                chunk = np.pad(chunk, (0, win - chunk.size))
            clipwise, _ = self.at.inference(chunk[None, :])
            scores.append(np.asarray(clipwise).reshape(-1))
        mat = np.vstack(scores)
        n, n_classes = mat.shape
        hop_ms = self.HOP_S * 1000.0

        def ratio(name: str, thr: float = 0.3) -> float:
            if name not in self.labels:
                return 0.0
            j = self.labels.index(name)
            return float(np.mean(mat[:, j] >= thr))

        music_ratio = ratio("Music", 0.3)
        speech_ratio = ratio("Speech", 0.3)
        event_cols = [i for i, l in enumerate(self.labels) if l not in EXCLUDE_EVENTS]
        event_ratio = float(np.mean(np.max(mat[:, event_cols], axis=1) >= 0.3))             if event_cols else 0.0

        candidates = [(i, float(mat[:, i].max())) for i in event_cols]
        candidates.sort(key=lambda x: x[1], reverse=True)
        candidates = [c for c in candidates if c[1] >= threshold][:max_classes]

        events: list[dict[str, Any]] = []
        for j, peak in candidates:
            label = self.labels[j]
            for a, b in _runs(mat[:, j] >= threshold, min_len=1, max_gap=1):
                start_ms = int(round(starts[a] / sr * 1000))
                end_ms = min(duration_ms, int(round((starts[b] + win) / sr * 1000)))
                if end_ms <= start_ms:
                    continue
                score = float(np.mean(mat[a:b + 1, j]))
                events.append({
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "label": label,
                    "label_zh": ZH.get(label, label),
                    "conf": round(score, 3),
                    "salience": round(float(peak), 3),
                    "source": "panns-cnn14-clip-window",
                })
        events.sort(key=lambda e: (e["start_ms"], -e["salience"]))
        for i, e in enumerate(events, 1):
            e["id"] = f"ev_{i:04d}"

        top = [{"label": self.labels[j], "label_zh": ZH.get(self.labels[j], self.labels[j]),
                "score": round(score, 3)} for j, score in candidates[:8]]
        return {
            "events": events,
            "music_ratio": round(music_ratio, 4),
            "speech_ratio": round(speech_ratio, 4),
            "event_ratio": round(event_ratio, 4),
            "top_labels": top,
            "frame_hop_ms": round(hop_ms, 3),
            "frames": n,
            "quality": "clip-window",
        }
