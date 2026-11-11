"""Rich context pack for a text LM to ask many questions from one Omni call."""
from __future__ import annotations

from typing import Any

from .fuse import display_label
from .media import fmt_ts


def build_context(score: dict[str, Any], *, max_chars: int = 12000, lang: str | None = None) -> str:
    g = score.get("global") or {}
    lines = ["SUMMARY: " + (g.get("summary") or (score.get("views") or {}).get("one_line") or "")]
    speech = (score.get("speech") or {}).get("segments") or []
    if speech:
        lines.append("\nTRANSCRIPT:")
        for s in speech[:500]:
            txt = (s.get("text") or "").strip()
            if txt:
                who = s.get("speaker") or "?"
                lines.append(f"[{fmt_ts(s['start_ms'])}-{fmt_ts(s['end_ms'])}] {who}: {txt}")
    events = score.get("events") or []
    if events:
        lines.append("\nEVENTS:")
        for e in events[:300]:
            lines.append(f"[{fmt_ts(e['start_ms'])}-{fmt_ts(e['end_ms'])}] "
                         f"{display_label(e, lang)} (precision={e.get('precision', 'omni-coarse')})")
    music = (score.get("music") or {}).get("tracks") or []
    if music:
        t = music[0]
        bits = []
        if t.get("bpm"):
            bits.append(f"{t['bpm']} BPM")
        if t.get("description"):
            bits.append(str(t["description"]))
        if t.get("beats_ms"):
            bits.append(f"{len(t['beats_ms'])} beats")
        lines.append("\nMUSIC: " + "; ".join(bits))
    warnings = score.get("warnings") or []
    if warnings:
        lines.append("\nCAVEATS:")
        lines.extend("- " + str(w) for w in warnings[:10])
    return "\n".join(lines)[:max_chars]
