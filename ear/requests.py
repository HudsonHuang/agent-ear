"""Turn a natural-language request into a lightweight execution plan."""
from __future__ import annotations

from dataclasses import dataclass, field

LABEL_HINTS = {
    "Laughter": ("laughter", "laugh", "giggle", "笑声", "笑"),
    "Applause": ("applause", "clap", "掌声", "鼓掌"),
    "Speech": ("speech", "talking", "说话", "人声"),
    "Music": ("music", "音乐", "歌"),
    "Glass": ("glass", "玻璃"),
    "Dog": ("dog", "bark", "狗"),
    "Gunshot, gunfire": ("gunshot", "gunfire", "枪声"),
    "Siren": ("siren", "警笛"),
    "Footsteps": ("footstep", "脚步"),
    "Cough": ("cough", "咳嗽"),
}


@dataclass
class RequestPlan:
    intent: str = "transcribe"          # transcribe | events | beat | music | privacy | qa
    labels: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    raw: str = ""


def parse_request(text: str | None) -> RequestPlan | None:
    if not text or not text.strip():
        return None
    t = text.lower()
    labels: list[str] = []
    for canon, hints in LABEL_HINTS.items():
        if any(h.lower() in t for h in hints):
            labels.append(canon)

    if any(k in t for k in ("隐私", "本地", "privacy", "offline")):
        return RequestPlan("privacy", labels, [], text)
    if any(k in t for k in ("卡点", "踩点", "节拍", "beat", "bpm", "cut to beat")):
        return RequestPlan("beat", labels, ["beat", "music"], text)
    if labels and any(k in t for k in ("剪", "切", "时间戳", "找", "提取", "所有", "全部", "cut", "extract", "find", "timestamp")):
        return RequestPlan("events", labels, ["events"], text)
    if any(k in t for k in ("音乐", "风格", "乐器", "music", "genre", "instrument")):
        return RequestPlan("music", labels, ["music"], text)
    if any(k in t for k in ("字幕", "转录", "逐字", "详细", "记录", "transcript", "subtitle", "captions")):
        return RequestPlan("transcribe", labels, ["transcript", "events"], text)
    if any(k in t for k in ("讲了什么", "说什么", "为什么", "问", "what", "why", "how")):
        return RequestPlan("qa", labels, [], text)
    return RequestPlan("transcribe", labels, ["transcript", "events"], text)
