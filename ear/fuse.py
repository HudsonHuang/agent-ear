"""Fusion: one clock, typed entities, relations, multi-resolution views."""
from __future__ import annotations

import os
from typing import Any

from .media import fmt_ts

MAX_TIMELINE = 800


def _overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def display_label(e: dict[str, Any], lang: str | None = None) -> str:
    """Event label in the requested language (default: EAR_LABEL_LANG or zh)."""
    lang = (lang or os.environ.get("EAR_LABEL_LANG", "zh")).lower()
    if lang == "en":
        return e.get("label") or e.get("label_zh") or "sound"
    return e.get("label_zh") or e.get("label") or "声音"


def _label_list(events: list[dict[str, Any]]) -> str:
    seen: list[str] = []
    for e in sorted(events, key=lambda x: -float(x.get("salience") or 0)):
        lab = display_label(e)
        if lab not in seen:
            seen.append(lab)
    return "、".join(seen[:4])


def merge_timeline(*, duration_ms: int, speech: list[dict[str, Any]],
                   events: list[dict[str, Any]], music: dict[str, Any] | None,
                   grid_ms: int = 10000) -> list[dict[str, Any]]:
    bounds = {0, duration_ms}
    for s in speech:
        bounds.add(max(0, int(s["start_ms"])))
        bounds.add(min(duration_ms, int(s["end_ms"])))
    for e in events:
        bounds.add(max(0, int(e["start_ms"])))
        bounds.add(min(duration_ms, int(e["end_ms"])))
    t = 0
    while t < duration_ms:
        bounds.add(t)
        t += grid_ms
    pts = sorted(bounds)
    out: list[dict[str, Any]] = []
    for a, b in zip(pts, pts[1:]):
        if b - a < 200:
            continue
        sp = [s for s in speech if _overlap(a, b, int(s["start_ms"]), int(s["end_ms"]))]
        ev = [e for e in events if _overlap(a, b, int(e["start_ms"]), int(e["end_ms"]))]
        has_music = bool(music and music.get("beats_ms"))
        speakers = sorted({s.get("speaker") for s in sp if s.get("speaker")})
        if sp:
            kind = "speech"
            text = " / ".join((s.get("text") or "").strip() for s in sp if s.get("text"))
            if not text:
                text = "语音（未转写）"
            if len(text) > 180:
                text = text[:177] + "…"
            if ev:
                text = f"{text}（同时：{_label_list(ev)}）" if text else f"（同时：{_label_list(ev)}）"
        elif ev:
            kind = "event"
            text = _label_list(ev)
        elif has_music:
            kind = "music"
            bpm = music.get("bpm") if music else None
            text = f"音乐 {bpm} BPM" if bpm else "音乐"
        else:
            kind = "silence"
            text = "静音/环境声"
        entry = {
            "start_ms": a,
            "end_ms": b,
            "kind": kind,
            "text": text,
            "refs": [s["id"] for s in sp] + [e["id"] for e in ev],
        }
        if len(speakers) == 1:
            entry["speaker"] = speakers[0]
        if ev:
            entry["events"] = [display_label(e) for e in ev]
        if has_music:
            entry["music"] = True
        if out and out[-1]["kind"] == entry["kind"] and out[-1]["text"] == entry["text"] \
                and out[-1]["refs"] == entry["refs"] and a - out[-1]["end_ms"] <= 120:
            out[-1]["end_ms"] = b
        else:
            out.append(entry)
    if len(out) > MAX_TIMELINE:
        # Coarsen by merging adjacent entries of the same kind until under the cap.
        merged: list[dict[str, Any]] = []
        step = max(1, len(out) // MAX_TIMELINE + 1)
        for i in range(0, len(out), step):
            chunk = out[i:i + step]
            merged.append({
                "start_ms": chunk[0]["start_ms"],
                "end_ms": chunk[-1]["end_ms"],
                "kind": chunk[0]["kind"],
                "text": "；".join(dict.fromkeys(c["text"] for c in chunk))[:240],
                "refs": [r for c in chunk for r in c["refs"]],
            })
        out = merged
    return out


def build_relations(*, speech: list[dict[str, Any]], events: list[dict[str, Any]],
                    music: dict[str, Any] | None) -> list[dict[str, Any]]:
    rels: list[dict[str, Any]] = []
    music_id = "mu_0001" if music and music.get("beats_ms") else None
    if music_id:
        for s in speech:
            rels.append({"type": "over", "from": s["id"], "to": music_id,
                         "conf": 0.9})
    # event after speech (gap <= 1.5s)
    for e in events:
        prev = None
        for s in speech:
            if int(s["end_ms"]) <= int(e["start_ms"]):
                if prev is None or int(s["end_ms"]) > int(prev["end_ms"]):
                    prev = s
            else:
                break
        if prev is not None:
            gap = int(e["start_ms"]) - int(prev["end_ms"])
            if 0 <= gap <= 1500:
                rels.append({"type": "after", "from": e["id"], "to": prev["id"],
                             "gap_ms": gap, "conf": min(0.95, 0.5 + e.get("conf", 0.5) / 2)})
    # cut candidates: downbeats near a speech/event boundary
    if music:
        bounds = [int(s["start_ms"]) for s in speech] + [int(s["end_ms"]) for s in speech]
        bounds += [int(e["start_ms"]) for e in events] + [int(e["end_ms"]) for e in events]
        for d in music.get("downbeats_ms") or []:
            d = int(d)
            near = [b for b in bounds if abs(b - d) <= 400]
            if near:
                rels.append({"type": "cut_candidate", "at_ms": d,
                             "reason": "downbeat near speech/event boundary",
                             "conf": 0.7})
            if len([r for r in rels if r["type"] == "cut_candidate"]) >= 80:
                break
    return rels


def build_views(*, duration_ms: int, speech: list[dict[str, Any]],
                events: list[dict[str, Any]], music: dict[str, Any] | None,
                timeline: list[dict[str, Any]], speakers: list[str]) -> dict[str, Any]:
    top = sorted(events, key=lambda e: -float(e.get("salience") or 0))[:5]
    parts = [f"时长 {duration_ms/60000:.1f} 分钟"]
    if speech:
        if speakers:
            parts.append(f"{len(speech)} 段语音 / {len(speakers)} 位说话人")
        else:
            parts.append(f"{len(speech)} 段语音 / 说话人未知")
    else:
        parts.append("无语音")
    if music and music.get("bpm"):
        parts.append(f"音乐 {music['bpm']} BPM")
    if top:
        parts.append("主要声音：" + "、".join(dict.fromkeys(display_label(e) for e in top)))
    one_line = "；".join(parts) + "。"

    chapters: list[dict[str, Any]] = []
    bucket = 60000
    t = 0
    while t < duration_ms:
        end = min(duration_ms, t + bucket)
        sp = [s for s in speech if _overlap(t, end, int(s["start_ms"]), int(s["end_ms"]))]
        ev = [e for e in events if _overlap(t, end, int(e["start_ms"]), int(e["end_ms"]))]
        title = ""
        if sp:
            title = ((sp[0].get("text") or "").strip() or "语音（未转写）")[:40]
        elif ev:
            title = _label_list(ev)
        else:
            title = "音乐/静音"
        chapters.append({"start_ms": t, "end_ms": end, "title": title})
        t = end
    if len(chapters) > 40:
        step = len(chapters) // 40 + 1
        chapters = [{"start_ms": c[0]["start_ms"], "end_ms": c[-1]["end_ms"],
                     "title": c[0]["title"]} for c in
                    [chapters[i:i + step] for i in range(0, len(chapters), step)]]

    # Coarse, human-readable timeline: 10s buckets (30s for very long files).
    bucket_ms = 10000 if duration_ms <= 10 * 60 * 1000 else 30000
    lines = []
    t = 0
    while t < duration_ms:
        end = min(duration_ms, t + bucket_ms)
        ents = [e for e in timeline
                if _overlap(t, end, int(e["start_ms"]), int(e["end_ms"]))]
        if not ents:
            t = end
            continue
        sp = [e for e in ents if e["kind"] == "speech"]
        ev = [e for e in ents if e["kind"] == "event"]
        mu = [e for e in ents if e["kind"] == "music"]
        if sp:
            tag = "人声"
            text = " / ".join(dict.fromkeys(
                (e.get("text") or "").strip() for e in sp if (e.get("text") or "").strip()))
            labels = []
            for e in ents:
                for lab in e.get("events") or []:
                    if lab not in labels:
                        labels.append(lab)
            if labels:
                text = (text + "（同时：" + "、".join(labels[:3]) + "）") if text else "、".join(labels[:3])
            if not text:
                text = "语音（未转写）"
        elif ev:
            tag = "事件"
            text = "、".join(dict.fromkeys(
                lab for e in ev for lab in (e.get("events") or [e.get("text")])
                if lab))
        elif mu:
            tag = "音乐"
            bpm = music.get("bpm") if music else None
            text = f"音乐 {bpm} BPM" if bpm else "音乐"
        else:
            tag = "静音"
            text = "静音/环境声"
        lines.append(f"{fmt_ts(t)}–{fmt_ts(end)} [{tag}] {text}")
        t = end
    return {
        "one_line": one_line,
        "chapters": chapters,
        "timeline_10s": lines[:400],
    }
