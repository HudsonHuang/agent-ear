"""Intent routing for basic / precise / privacy."""
from __future__ import annotations

from typing import Any

NEEDS = ("transcript", "events", "beat", "music")
KEYWORDS = {
    "transcript": ("字幕", "转录", "逐字", "打轴", "时间戳", "subtitle", "transcript", "caption", "word"),
    "events": ("笑声", "掌声", "事件", "音效", "精确", "laughter", "applause", "event", "sound"),
    "beat": ("卡点", "踩点", "节拍", "beat", "bpm", "cut", "剪辑点"),
    "music": ("音乐", "歌", "乐器", "风格", "music", "song", "instrument", "genre"),
}


def parse_needs(raw: str | None, *, mode: str) -> list[str]:
    if raw:
        if raw.strip().lower() == "none":
            return []
        out = [x.strip() for x in raw.split(",") if x.strip()]
        bad = [x for x in out if x not in NEEDS]
        if bad:
            raise ValueError(f"unknown needs: {bad}; choose from {NEEDS}")
        return out
    if mode == "precise":
        return ["transcript", "events", "beat"]
    if mode == "music":
        return ["music", "beat"]
    return []


def plan(mode: str, needs: list[str], omni: dict[str, Any] | None) -> dict[str, bool]:
    has_speech = bool((omni or {}).get("segments"))
    has_events = bool((omni or {}).get("events"))
    has_music = bool(((omni or {}).get("music") or {}).get("present"))
    if mode == "basic" or mode == "default":
        return {"omni": True, "asr": False, "aed": False, "beat": False}
    if mode == "privacy":
        return {"omni": False, "asr": False, "aed": True, "beat": True}
    # precise and music
    return {
        "omni": True,
        "asr": has_speech and "transcript" in needs,
        "aed": has_events and "events" in needs,
        "beat": has_music and ("beat" in needs or mode == "music"),
    }
