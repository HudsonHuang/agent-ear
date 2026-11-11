"""Qwen3.8-Omni-Flash provider.

One audio call returns a normalized semantic analysis: transcript segments,
events, music description. Long audio is chunked (10 min) and offsets merged.
"""
from __future__ import annotations

import base64
import json
from concurrent.futures import ThreadPoolExecutor
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from . import media

MODEL = os.environ.get("OMNI_MODEL", "qwen3.8-omni-flash")
CHUNK_S = 120.0
PROMPT = (
    "Analyze this audio for a video editor. Return ONLY a JSON object:\n"
    '{"summary":"one paragraph",'
    '"segments":[{"start":0.0,"end":1.0,"speaker":"S1","text":"verbatim original language"}],'
    '"events":[{"start":0.0,"end":1.0,"label":"laughter|applause|music|glass breaking|..."}],'
    '"music":{"present":true,"description":"genre/mood/instruments","bpm":null}}\n'
    "Rules: transcribe verbatim in the ORIGINAL language, do NOT translate. "
    "Timestamps in seconds with 0.1 precision. Only include events you actually hear. "
    "Do not invent. No markdown fences."
)


def _events_prompt(targets: list[str] | None) -> str:
    labels = ", ".join(targets or ["Laughter", "Applause", "Speech", "Music"])
    return (
        "Find EVERY occurrence of these sound events in the audio: " + labels + ". "
        "Return ONLY a JSON object: "
        '{"summary":"one sentence",'
        '"events":[{"start":0.0,"end":1.0,"label":"Laughter","confidence":0.9}]}. '
        "Include short events. Timestamps in seconds with 0.1 precision. "
        "Only events you actually hear. Do not transcribe speech. No markdown fences."
    )


def _prompt(question: str | None = None, choices: list[str] | None = None) -> str:
    if not question:
        return PROMPT
    out = PROMPT + ("\nThe JSON MUST also contain the `answer` field, in addition to the full analysis. "
                    "Put `answer` as the FIRST field of the JSON object, before `summary`. ")
    if choices:
        out += ("For the multiple-choice QUESTION, answer with exactly one letter A/B/C/D "
                "in `answer`.\n")
    else:
        out += "Answer the QUESTION concisely in `answer`, using the original language of the question.\n"
    out += f"QUESTION: {question}\n"
    if choices:
        out += "\n".join(f"{'ABCD'[i]}. {c}" for i, c in enumerate(choices)) + "\n"
    return out


class OmniError(RuntimeError):
    pass


def _cfg() -> tuple[str, str]:
    from . import config
    q = config.get_qwen()
    base = (os.environ.get("OMNI_BASE_URL") or config.omni_base()).rstrip("/")
    key = os.environ.get("OMNI_API_KEY") or q.get("api_key") or ""
    if not key:
        raise OmniError("Qwen API key is not configured; run `agent-ear setup` or set DASHSCOPE_API_KEY")
    return base, key


def _model() -> str:
    from . import config
    return os.environ.get("OMNI_MODEL") or config.get_qwen().get("omni_model") or MODEL


def _mp3(src: Path, dst: Path, start: float = 0, dur: float | None = None) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [media.FFMPEG, "-y", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", str(src)]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k", str(dst)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not dst.is_file():
        raise OmniError(f"mp3 encode failed: {p.stderr[-500:]}")
    return dst


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise OmniError(f"no JSON in Omni response: {text[:300]}")
    return json.loads(m.group(0))


def _call(base: str, key: str, audio: Path, prompt: str,
          thinking: int = 256, max_tokens: int = 8000) -> tuple[dict, dict, float]:
    data = base64.b64encode(audio.read_bytes()).decode()
    body = {
        "model": _model(),
        "messages": [{"role": "user", "content": [
            {"type": "input_audio",
             "input_audio": {"data": f"data:audio/mpeg;base64,{data}", "format": "mp3"}},
            {"type": "text", "text": prompt},
        ]}],
        "modalities": ["text"],
        "max_tokens": max_tokens,
        "temperature": 0,
        "enable_thinking": thinking > 0,
    }
    if thinking > 0:
        body["thinking_budget"] = thinking
    t = time.time()
    r = requests.post(f"{base}/chat/completions",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json=body, timeout=900)
    if r.status_code >= 300:
        raise OmniError(f"Omni {r.status_code}: {r.text[:500]}")
    d = r.json()
    wall = time.time() - t
    content = (d["choices"][0]["message"].get("content") or "").strip()
    return _parse_json(content), d.get("usage") or {}, wall


def _norm_chunk(raw: dict, offset_ms: int, duration_ms: int) -> dict[str, Any]:
    segs = []
    for s in raw.get("segments") or []:
        try:
            a = int(round(float(s.get("start")) * 1000)) + offset_ms
            b = int(round(float(s.get("end")) * 1000)) + offset_ms
        except Exception:
            continue
        text = (s.get("text") or "").strip()
        if b <= a or not text:
            continue
        segs.append({"start_ms": max(0, a), "end_ms": min(duration_ms, b),
                     "speaker": str(s.get("speaker") or "S1"), "text": text,
                     "lang": "", "conf": None, "words": [], "source": "omni"})
    events = []
    for e in raw.get("events") or []:
        try:
            a = int(round(float(e.get("start")) * 1000)) + offset_ms
            b = int(round(float(e.get("end")) * 1000)) + offset_ms
        except Exception:
            continue
        label = (e.get("label") or "").strip()
        if b <= a or not label:
            continue
        events.append({"start_ms": max(0, a), "end_ms": min(duration_ms, b),
                       "label": label, "conf": e.get("confidence", 0.7),
                       "salience": 0.7, "source": "omni",
                       "precision": "omni-coarse"})
    m = raw.get("music") or {}
    return {"segments": segs, "events": events,
            "music": {"present": bool(m.get("present")), "description": m.get("description") or "",
                      "bpm": m.get("bpm")}, "summary": (raw.get("summary") or "").strip(),
            "answer": (raw.get("answer") or "").strip()}


def analyze(audio: Path, *, thinking: int = 256, max_tokens: int = 8000,
            chunk_s: float = CHUNK_S, question: str | None = None,
            choices: list[str] | None = None, profile: str = "full",
            targets: list[str] | None = None) -> dict[str, Any]:
    base, key = _cfg()
    info = media.media_info(audio)
    duration_ms = int(info["duration_ms"])
    tmp = Path(tempfile.mkdtemp(prefix="ear-omni-"))
    chunks: list[Path] = []
    offsets: list[int] = []
    try:
        overlap = 2.0 if profile == "events" else 0.0
        step = max(20.0, chunk_s - overlap)
        if duration_ms <= int(chunk_s * 1000):
            chunks = [_mp3(audio, tmp / "chunk_000.mp3")]
            offsets = [0]
        else:
            n = 0
            t = 0.0
            while t < duration_ms / 1000:
                dur = min(chunk_s, duration_ms / 1000 - t)
                chunks.append(_mp3(audio, tmp / f"chunk_{n:03d}.mp3", t, dur))
                offsets.append(int(round(t * 1000)))
                t += step
                n += 1
        out = {"provider": _model(), "profile": profile, "targets": targets or [],
               "segments": [], "events": [],
               "music": {"present": False, "description": "", "bpm": None},
               "summary": "", "answer": "", "usage": {}, "wall_s": 0.0, "chunks": len(chunks)}
        summaries = []
        prompt = _events_prompt(targets) if profile == "events" else _prompt(question, choices)
        def one(i: int, c: Path):
            raw, usage, wall = _call(base, key, c, prompt, thinking, max_tokens)
            return i, raw, usage, wall
        with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as ex:
            results = list(ex.map(lambda ic: one(*ic), enumerate(chunks)))
        for i, raw, usage, wall in results:
            off = offsets[i] if i < len(offsets) else int(round(i * step * 1000))
            part = _norm_chunk(raw, off, duration_ms)
            out["segments"] += part["segments"]
            out["events"] += part["events"]
            if part["summary"]:
                summaries.append(part["summary"])
            if part.get("answer") and not out["answer"]:
                out["answer"] = part["answer"]
            if part["music"].get("present") and not out["music"]["present"]:
                out["music"] = part["music"]
            for k, v in usage.items():
                if isinstance(v, (int, float)):
                    out["usage"][k] = out["usage"].get(k, 0) + v
            out["wall_s"] += wall
        out["summary"] = " ".join(summaries).strip()
        if question and len(chunks) > 1:
            out["warnings"] = ["question answer comes from the first chunk with an answer; for long audio prefer analysis + text follow-up"]
        out["segments"].sort(key=lambda s: s["start_ms"])
        merged: list[dict[str, Any]] = []
        for e in sorted(out["events"], key=lambda x: x["start_ms"]):
            if merged and e.get("label") == merged[-1].get("label") and \
                    int(e["start_ms"]) <= int(merged[-1]["end_ms"]) + 300:
                merged[-1]["end_ms"] = max(int(merged[-1]["end_ms"]), int(e["end_ms"]))
                merged[-1]["conf"] = max(float(merged[-1].get("conf") or 0), float(e.get("conf") or 0))
            else:
                merged.append(e)
        out["events"] = merged
        for i, s in enumerate(out["segments"], 1):
            s["id"] = f"sp_{i:04d}"
        for i, e in enumerate(out["events"], 1):
            e["id"] = f"ev_{i:04d}"
        return out
    finally:
        for c in chunks:
            try:
                c.unlink()
            except OSError:
                pass
        try:
            tmp.rmdir()
        except OSError:
            pass


def ask(audio: Path, question: str, *, thinking: int = 256,
        max_tokens: int = 1200) -> dict[str, Any]:
    """Direct audio Q&A (no JSON schema); this is the high-accuracy basic path."""
    base, key = _cfg()
    tmp = Path(tempfile.mkdtemp(prefix="ear-omni-"))
    try:
        c = _mp3(audio, tmp / "a.mp3")
        data = base64.b64encode(c.read_bytes()).decode()
        body = {"model": _model(), "messages": [{"role": "user", "content": [
            {"type": "input_audio",
             "input_audio": {"data": f"data:audio/mpeg;base64,{data}", "format": "mp3"}},
            {"type": "text", "text": question}]}],
            "modalities": ["text"], "max_tokens": max_tokens, "temperature": 0,
            "enable_thinking": thinking > 0}
        if thinking > 0:
            body["thinking_budget"] = thinking
        t = time.time()
        r = requests.post(f"{base}/chat/completions",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json=body, timeout=600)
        if r.status_code >= 300:
            raise OmniError(f"Omni {r.status_code}: {r.text[:400]}")
        d = r.json()
        return {"content": (d["choices"][0]["message"].get("content") or "").strip(),
                "usage": d.get("usage") or {}, "wall_s": round(time.time() - t, 2),
                "model": _model()}
    finally:
        for f in tmp.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            tmp.rmdir()
        except OSError:
            pass


def answer(audio: Path, question: str, choices: list[str], *,
           thinking: int = 256, max_tokens: int = 20) -> tuple[str | None, dict, float]:
    base, key = _cfg()
    tmp = Path(tempfile.mkdtemp(prefix="ear-omni-"))
    try:
        c = _mp3(audio, tmp / "a.mp3")
        prompt = ("Listen and answer the multiple-choice question. "
                  "Reply with exactly one letter A/B/C/D and nothing else.\n"
                  f"Question: {question}\n" +
                  "\n".join(f"{'ABCD'[i]}. {ch}" for i, ch in enumerate(choices)) +
                  "\nAnswer:")
        data = base64.b64encode(c.read_bytes()).decode()
        body = {"model": _model(), "messages": [{"role": "user", "content": [
            {"type": "input_audio",
             "input_audio": {"data": f"data:audio/mpeg;base64,{data}", "format": "mp3"}},
            {"type": "text", "text": prompt}]}],
            "modalities": ["text"], "max_tokens": max_tokens, "temperature": 0,
            "enable_thinking": thinking > 0}
        if thinking > 0:
            body["thinking_budget"] = thinking
        t = time.time()
        r = requests.post(f"{base}/chat/completions",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json=body, timeout=300)
        d = r.json()
        raw = (d["choices"][0]["message"].get("content") or "").strip()
        m = re.search(r"\b([ABCD])\b", raw.upper())
        return (m.group(1) if m else None), d.get("usage") or {}, time.time() - t
    finally:
        for f in tmp.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            tmp.rmdir()
        except OSError:
            pass
