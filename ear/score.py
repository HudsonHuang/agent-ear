"""Build/refine audio-score from Omni analysis + local precision layers."""
from __future__ import annotations

from typing import Any

from . import __version__, fuse
from .events_panns import ZH
from .media import fmt_ts


def _turns(segments: list[dict[str, Any]], gap_ms: int = 600) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for s in segments:
        if turns and turns[-1]["speaker"] == s["speaker"] and \
                int(s["start_ms"]) - turns[-1]["end_ms"] <= gap_ms:
            turns[-1]["end_ms"] = s["end_ms"]
            turns[-1]["texts"].append(s.get("text") or "")
        else:
            turns.append({"speaker": s["speaker"], "start_ms": s["start_ms"],
                          "end_ms": s["end_ms"], "texts": [s.get("text") or ""]})
    for t in turns:
        t["text"] = " ".join(x for x in t["texts"] if x).strip()
        t.pop("texts", None)
    return turns


def _label(e: dict[str, Any]) -> str:
    return e.get("label_zh") or e.get("label") or "event"


def _canon_label(label: str) -> str:
    if label in ZH:
        return label
    low = (label or "").lower()
    for k in ZH:
        if k.lower() == low:
            return k
    return label


def _decorate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i, e in enumerate(events, 1):
        e = dict(e)
        e["omni_label"] = e.get("label", "")
        e["label"] = _canon_label(e.get("label", ""))
        e["id"] = e.get("id") or f"ev_{i:04d}"
        e["label_zh"] = e.get("label_zh") or ZH.get(e.get("label", ""), e.get("label", ""))
        e.setdefault("conf", 0.7)
        e.setdefault("salience", 0.7)
        e.setdefault("precision", "omni-coarse")
        e.setdefault("source", "omni")
        out.append(e)
    return out


def finalize(score: dict[str, Any]) -> dict[str, Any]:
    duration = int(score["source"]["duration_ms"])
    speech = score.setdefault("speech", {}).setdefault("segments", [])
    events = score.setdefault("events", [])
    tracks = score.setdefault("music", {}).setdefault("tracks", [])
    music = tracks[0] if tracks else None
    score["speech"]["turns"] = _turns(speech)
    score["speech"]["non_speech_vocal"] = [
        e for e in events if e.get("label") in
        {"Laughter", "Crying, sobbing", "Sigh", "Cough", "Sneeze", "Breathing", "Gasp"}
    ]
    score["timeline"] = fuse.merge_timeline(
        duration_ms=duration, speech=speech, events=events, music=music)
    score["relations"] = fuse.build_relations(
        speech=speech, events=events, music=music)
    speakers = sorted({s.get("speaker") for s in speech if s.get("speaker")})
    langs = sorted({s.get("lang") for s in speech if s.get("lang")})
    views = fuse.build_views(
        duration_ms=duration, speech=speech, events=events, music=music,
        timeline=score["timeline"], speakers=speakers)
    score["views"] = views
    g = score.setdefault("global", {})
    g["summary"] = g.get("summary") or views["one_line"]
    g["duration_ms"] = duration
    g["speech_ratio"] = round(sum(max(0, s["end_ms"] - s["start_ms"]) for s in speech) / max(1, duration), 4)
    g["music_ratio"] = 1.0 if music else 0.0
    g["event_ratio"] = round(min(1.0, sum(max(0, e["end_ms"] - e["start_ms"]) for e in events)
                                 / max(1, duration)), 4)
    g["speakers"] = len(speakers)
    g["languages"] = langs
    g.setdefault("scene", "unknown")
    g.setdefault("mood_curve", [])
    g["top_sounds"] = sorted(events, key=lambda e: -float(e.get("salience") or 0))[:10]
    return score


def from_omni(omni: dict[str, Any], *, source_path: str, sha256: str,
              duration_ms: int, mode: str = "basic",
              elapsed_s: float = 0.0) -> dict[str, Any]:
    events = _decorate_events(list(omni.get("events") or []))
    speech = []
    for i, s in enumerate(omni.get("segments") or [], 1):
        s = dict(s)
        s["id"] = s.get("id") or f"sp_{i:04d}"
        s.setdefault("words", [])
        s.setdefault("conf", None)
        s.setdefault("source", "omni")
        speech.append(s)
    m = omni.get("music") or {}
    tracks = []
    if m.get("present"):
        tracks.append({
            "id": "mu_0001", "start_ms": 0, "end_ms": duration_ms,
            "bpm": m.get("bpm"), "beats_ms": [], "downbeats_ms": [],
            "beat_positions": [], "sections": [], "genre": None,
            "mood": None, "instruments": [], "vocals": None,
            "quality": "omni", "description": m.get("description") or "",
        })
    score: dict[str, Any] = {
        "schema": "ear.score/1",
        "source": {"path": source_path, "sha256": sha256, "duration_ms": duration_ms,
                   "fps": None, "pts_offset_ms": 0, "trimmed_to_ms": None},
        "capabilities": {
            "omni": omni.get("provider") or "qwen3.8-omni-flash",
            "speech": "omni" if speech else None,
            "events": "omni" if events else None,
            "music": "omni" if tracks else None,
            "fusion": "rules-v1",
        },
        "global": {
            "summary": omni.get("summary") or "",
            "scene": "unknown",
            "mood_curve": [],
            "mode": mode,
        },
        "speech": {"segments": speech, "turns": [], "non_speech_vocal": []},
        "music": {"tracks": tracks, "lyrics": []},
        "events": events,
        "relations": [],
        "timeline": [],
        "views": {"one_line": "", "chapters": [], "timeline_10s": []},
        "warnings": [],
        "provenance": {
            "tool_version": __version__,
            "elapsed_s": round(elapsed_s, 2),
            "omni": {"usage": omni.get("usage") or {}, "wall_s": omni.get("wall_s"),
                     "chunks": omni.get("chunks"), "profile": omni.get("profile"),
                     "targets": omni.get("targets") or []},
        },
    }
    warnings = score["warnings"]
    warnings.append("Omni timestamps are coarse (0.5–2s); use precise mode for word/beat timing")
    if (omni.get("profile") or "full") == "events":
        warnings.append("event-only profile: speech/transcript not extracted; use full profile if you need it")
    if duration_ms > 10 * 60 * 1000:
        warnings.append("long audio: hearing.md may be large; use digest/one_line for LM context")
    if duration_ms < 90000 and speech:
        warnings.append("file <90s: speaker labels may collapse; treat as anonymous")
    return finalize(score)


_ALIASES = {
    "laughter": "Laughter", "laugh": "Laughter", "giggle": "Laughter",
    "applause": "Applause", "clapping": "Applause", "clap": "Applause",
    "glass": "Glass", "glass breaking": "Glass", "shatter": "Glass",
    "footsteps": "Footsteps", "footstep": "Footsteps",
    "door": "Door", "knock": "Knock", "dog": "Dog", "bark": "Dog",
    "gunshot": "Gunshot, gunfire", "explosion": "Explosion",
    "siren": "Siren", "alarm": "Alarm", "typing": "Typing", "keyboard": "Typing",
    "cough": "Cough", "sneeze": "Sneeze", "breathing": "Breathing",
    "music": "Music", "speech": "Speech", "singing": "Singing",
}


def _target_label(label: str) -> str | None:
    lab = (label or "").strip().lower()
    if lab in _ALIASES:
        return _ALIASES[lab]
    for k, v in _ALIASES.items():
        if k in lab:
            return v
    return None


def refine_events(score: dict[str, Any], local_events: list[dict[str, Any]]) -> int:
    """Refine Omni event boundaries with local 40ms AED events.

    Only events already proposed by Omni are touched; local false positives
    outside those windows never enter the score.
    """
    by_label: dict[str, list[dict[str, Any]]] = {}
    for e in local_events:
        by_label.setdefault(e.get("label", ""), []).append(e)
    refined = 0
    for e in score.get("events") or []:
        target = _target_label(e.get("label", ""))
        if not target:
            continue
        cands = by_label.get(target) or []
        if not cands:
            continue
        a, b = int(e["start_ms"]), int(e["end_ms"])
        best = None
        best_ov = 0
        for c in cands:
            ov = max(0, min(b, int(c["end_ms"])) - max(a, int(c["start_ms"])))
            if ov > best_ov:
                best, best_ov = c, ov
        if best is None or best_ov <= 0:
            continue
        e["omni_start_ms"], e["omni_end_ms"] = a, b
        e["start_ms"], e["end_ms"] = int(best["start_ms"]), int(best["end_ms"])
        e["conf"] = best.get("conf", e.get("conf"))
        e["salience"] = max(float(e.get("salience") or 0), float(best.get("salience") or 0))
        e["precision"] = "refined-40ms"
        e["refined_by"] = "pretrainedsed-beats-strong"
        refined += 1
    if refined:
        score["capabilities"]["events"] = "omni+refined"
    return refined


def apply_asr(score: dict[str, Any], asr: dict[str, Any]) -> None:
    segs = []
    for i, s in enumerate(asr.get("segments") or [], 1):
        s = dict(s)
        s["id"] = f"sp_{i:04d}"
        s["source"] = "qwen-asr"
        segs.append(s)
    if segs:
        score["speech"]["omni_transcript"] = [
            {"start_ms": s["start_ms"], "end_ms": s["end_ms"], "text": s.get("text", "")}
            for s in score["speech"].get("segments") or []
        ]
        score["speech"]["segments"] = segs
        score["capabilities"]["speech"] = "qwen-asr"


def apply_beats(score: dict[str, Any], bt: dict[str, Any], duration_ms: int) -> None:
    tracks = score["music"].setdefault("tracks", [])
    if tracks:
        t = tracks[0]
    else:
        t = {"id": "mu_0001", "start_ms": 0, "end_ms": duration_ms,
             "genre": None, "mood": None, "instruments": [], "vocals": None,
             "description": ""}
        tracks.append(t)
    t.update({
        # Keep Omni's estimate when the beat tracker returns no tempo.
        "bpm": bt.get("bpm") or t.get("bpm"), "beats_ms": bt.get("beats_ms") or [],
        "downbeats_ms": bt.get("downbeats_ms") or [],
        "beat_positions": bt.get("beat_positions") or [],
        "quality": bt.get("quality"), "provider": bt.get("provider"),
    })
    score["capabilities"]["music"] = bt.get("provider") or "beat-this"
