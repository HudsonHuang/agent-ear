"""Small text-LLM helper for asking questions against a saved context pack."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests

DEFAULT_MODEL = os.environ.get("EAR_TEXT_MODEL", "qwen-plus")


def _cfg() -> tuple[str, str]:
    from . import config
    q = config.get_qwen()
    base = (os.environ.get("EAR_TEXT_BASE_URL") or config.text_base()).rstrip("/")
    key = os.environ.get("EAR_TEXT_API_KEY") or q.get("api_key") or ""
    if not key:
        raise RuntimeError("Qwen API key is not configured; run `agent-ear setup` or set DASHSCOPE_API_KEY")
    return base, key


def answer(context: str, question: str, choices: list[str] | None = None,
           model: str | None = None, max_tokens: int = 64) -> dict:
    base, key = _cfg()
    model = model or DEFAULT_MODEL
    system = ("You answer questions using the audio context below. The context is a transcript/event "
              "timeline from an audio analysis system; it may be incomplete. Answer concisely.")
    user = f"Audio context:\n{context}\n\nQuestion: {question}"
    if choices:
        user += "\n" + "\n".join(f"{'ABCD'[i]}. {c}" for i, c in enumerate(choices))
        user += "\nReply with exactly one letter A/B/C/D."
    payload = {"model": model, "messages": [{"role": "system", "content": system},
                                           {"role": "user", "content": user}],
               "temperature": 0, "max_tokens": max_tokens}
    r = requests.post(f"{base}/chat/completions",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json=payload, timeout=120)
    if r.status_code >= 300:
        raise RuntimeError(f"text LLM {r.status_code}: {r.text[:300]}")
    d = r.json()
    raw = (d["choices"][0]["message"].get("content") or "").strip()
    letter = None
    if choices:
        m = re.search(r"\b([ABCD])\b", raw.upper())
        letter = m.group(1) if m else None
    return {"content": raw, "letter": letter, "model": model,
            "usage": d.get("usage") or {}}
