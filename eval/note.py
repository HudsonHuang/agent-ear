"""Build a question-aware evidence note from audio-score.json."""
from __future__ import annotations

from typing import Any

from ear.fuse import display_label
from ear.media import fmt_ts

SPEECH_HINTS = (
    "say", "said", "speak", "talk", "mean", "according", "word", "phrase",
    "language", "voice", "speaker", "conversation", "dialogue", "transcript",
    "问", "说", "讲", "意思", "根据", "话", "语言", "对话", "内容", "提到",
)
SOUND_HINTS = (
    "sound", "noise", "hear", "background", "event", "effect", "sfx",
    "声", "音效", "背景", "事件", "听到", "噪音",
)
MUSIC_HINTS = (
    "music", "song", "instrument", "genre", "tempo", "beat", "melody",
    "音乐", "歌", "乐器", "风格", "节拍", "旋律",
)


def build_note(score: dict[str, Any], question: str, *, lang: str = "zh",
               max_chars: int = 6000) -> str:
    q = question.lower()
    g = score.get("global") or {}
    views = score.get("views") or {}
    speech = (score.get("speech") or {}).get("segments") or []
    events = score.get("events") or []
    tracks = (score.get("music") or {}).get("tracks") or []
    top = g.get("top_sounds") or []
    parts: list[str] = []
    parts.append("SUMMARY: " + (views.get("one_line") or g.get("summary") or ""))

    wants_speech = any(h in q for h in SPEECH_HINTS) or not events
    wants_sound = any(h in q for h in SOUND_HINTS)
    wants_music = any(h in q for h in MUSIC_HINTS) or bool(tracks)

    if speech:
        lines = []
        for s in speech[:100]:
            text = (s.get("text") or "").strip()
            if text:
                who = s.get("speaker") or "?"
                lines.append(f"{fmt_ts(s['start_ms'])} {who}: {text}")
        if lines:
            parts.append("TRANSCRIPT:\n" + "\n".join(lines))

    if events:
        lines = []
        for e in events[:40]:
            lines.append(f"{fmt_ts(e['start_ms'])}-{fmt_ts(e['end_ms'])} "
                         f"{display_label(e, lang)} (conf {e.get('conf', '')})")
        if lines:
            parts.append("EVENTS:\n" + "\n".join(lines))

    if tracks:
        t = tracks[0]
        bits = []
        if t.get("bpm"):
            bits.append(f"{t['bpm']} BPM")
        if t.get("beats_ms"):
            bits.append(f"{len(t['beats_ms'])} beats")
        parts.append("MUSIC: " + ("; ".join(bits) if bits else "present"))

    if top:
        labs = []
        for t in top[:10]:
            lab = display_label(t, lang)
            if lab not in labs:
                labs.append(lab)
        parts.append("SOUND TAGS: " + ", ".join(labs))

    if not parts:
        parts.append("No reliable evidence was extracted.")

    out = "\n\n".join(parts)
    return out[:max_chars]
