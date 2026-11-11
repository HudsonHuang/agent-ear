"""Editor-facing exports: SRT, CMX3600 EDL, and ranked highlights."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_score(path: str | Path) -> tuple[dict[str, Any], Path]:
    p = Path(path).expanduser()
    if p.is_dir():
        p = p / "audio-score.json"
    if not p.is_file():
        raise FileNotFoundError(f"score not found: {p}")
    return json.loads(p.read_text(encoding="utf-8")), p


def _fmt_srt(ms: int) -> str:
    ms = max(0, int(round(ms)))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_tc(ms: int, fps: float) -> str:
    frames_total = max(0, int(round(ms / 1000 * fps)))
    fps_i = max(1, int(round(fps)))
    f = frames_total % fps_i
    total_s = frames_total // fps_i
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def _label(event: dict[str, Any]) -> str:
    return (event.get("label_zh") or event.get("label") or "sound").strip()


def _match(event: dict[str, Any], labels: list[str] | None) -> bool:
    if not labels:
        return True
    raw = f"{event.get('label','')} {event.get('label_zh','')}".lower()
    return any(x.lower() in raw for x in labels)


def srt(score: dict[str, Any], *, sdh: bool = True, speaker: bool = False) -> str:
    cues: list[tuple[int, int, str]] = []
    for s in (score.get("speech") or {}).get("segments") or []:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        if speaker and s.get("speaker"):
            text = f"{s['speaker']}: {text}"
        cues.append((int(s["start_ms"]), int(s["end_ms"]), text))
    if sdh:
        for e in score.get("events") or []:
            lab = _label(e)
            if lab in ("Speech", "说话", "Music", "音乐"):
                continue
            a, b = int(e["start_ms"]), int(e["end_ms"])
            if b <= a:
                continue
            cues.append((a, b, f"[{lab}]"))
    cues.sort(key=lambda x: (x[0], x[1]))
    lines: list[str] = []
    for i, (a, b, text) in enumerate(cues, 1):
        if b <= a:
            b = a + 1
        lines += [str(i), f"{_fmt_srt(a)} --> {_fmt_srt(b)}", text, ""]
    return "\n".join(lines)


def edl(score: dict[str, Any], *, labels: list[str] | None = None,
        fps: float | None = None, pad_before: int = 0, pad_after: int = 0,
        title: str = "agent-ear") -> str:
    fps = float(fps or (score.get("source") or {}).get("fps") or 30.0)
    events = [e for e in (score.get("events") or []) if _match(e, labels)]
    if not events:
        raise ValueError("no matching events for EDL")
    duration = int((score.get("source") or {}).get("duration_ms") or 0)
    lines = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]
    rec = 0
    for i, e in enumerate(sorted(events, key=lambda x: int(x["start_ms"])), 1):
        a = max(0, int(e["start_ms"]) - pad_before)
        b = min(duration or 10**12, int(e["end_ms"]) + pad_after)
        if b <= a:
            continue
        lines.append(
            f"{i:03d}  AX       V     C        "
            f"{_fmt_tc(a, fps)} {_fmt_tc(b, fps)} {_fmt_tc(rec, fps)} {_fmt_tc(rec + b - a, fps)}"
        )
        lines.append(f"* FROM CLIP NAME: {_label(e)}")
        lines.append("")
        rec += b - a
    return "\n".join(lines)


def highlights(score: dict[str, Any], *, top: int = 5, by: list[str] | None = None,
               pad_before: int = 300, pad_after: int = 500, min_gap: int = 400) -> list[dict[str, Any]]:
    duration = int((score.get("source") or {}).get("duration_ms") or 0)
    cands: list[dict[str, Any]] = []
    for e in score.get("events") or []:
        if not _match(e, by):
            continue
        conf = float(e.get("conf") or 0.5)
        sal = float(e.get("salience") or 0.5)
        a = max(0, int(e["start_ms"]) - pad_before)
        b = min(duration or 10**12, int(e["end_ms"]) + pad_after)
        if b <= a:
            continue
        cands.append({"start_ms": a, "end_ms": b, "label": _label(e),
                      "score": round(0.6 * sal + 0.4 * conf, 4),
                      "source_event": e.get("id")})
    cands.sort(key=lambda x: (-x["score"], x["start_ms"]))
    picked: list[dict[str, Any]] = []
    for c in cands:
        conflict = any(not (c["end_ms"] < p["start_ms"] - min_gap or
                            c["start_ms"] > p["end_ms"] + min_gap) for p in picked)
        if not conflict:
            c["rank"] = len(picked) + 1
            picked.append(c)
        if len(picked) >= top:
            break
    return picked


def highlights_md(score: dict[str, Any], items: list[dict[str, Any]]) -> str:
    lines = ["# agent-ear highlights", ""]
    for x in items:
        lines.append(f"{x['rank']}. **{_fmt_srt(x['start_ms'])} → {_fmt_srt(x['end_ms'])}** "
                     f"{x['label']}  score={x['score']}")
    return "\n".join(lines) + "\n"
