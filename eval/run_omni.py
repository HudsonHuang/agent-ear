"""Qwen3.8-Omni-Flash single-model baseline.

Modes:
  answer  - audio + question + choices -> one letter (tests ASR+understanding)
  analyze - audio -> structured JSON (tests ASR/timestamps/events/music)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
LETTERS = "ABCD"


def cfg() -> tuple[str, str]:
    base = (os.environ.get("OMNI_BASE_URL") or "").rstrip("/")
    key = os.environ.get("OMNI_API_KEY") or ""
    if not base or not key:
        p = Path.home() / ".bailian" / "config.json"
        c = json.loads(p.read_text(encoding="utf-8"))
        base = base or (str(c["base_url"]).rstrip("/") + "/compatible-mode/v1")
        key = key or str(c["api_key"])
    return base, key


def call(base: str, key: str, audio: Path, prompt: str, max_tokens: int,
         thinking_budget: int = 0) -> tuple[dict, float]:
    data = base64.b64encode(audio.read_bytes()).decode()
    body = {
        "model": os.environ.get("OMNI_MODEL", "qwen3.8-omni-flash"),
        "messages": [{"role": "user", "content": [
            {"type": "input_audio",
             "input_audio": {"data": f"data:audio/wav;base64,{data}", "format": "wav"}},
            {"type": "text", "text": prompt},
        ]}],
        "modalities": ["text"],
        "max_tokens": max_tokens,
        "temperature": 0,
        "enable_thinking": thinking_budget > 0,
    }
    if thinking_budget > 0:
        body["thinking_budget"] = thinking_budget
    t = time.time()
    r = requests.post(f"{base}/chat/completions",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json=body, timeout=600)
    if r.status_code >= 300:
        raise RuntimeError(f"Omni {r.status_code}: {r.text[:400]}")
    return r.json(), time.time() - t


def parse_letter(text: str) -> str | None:
    m = re.search(r"\b([ABCD])\b", (text or "").upper())
    return m.group(1) if m else None


def answer_one(item: dict[str, Any], base: str, key: str,
               thinking_budget: int = 0) -> dict[str, Any]:
    choices = "\n".join(f"{LETTERS[i]}. {c}" for i, c in enumerate(item["choices"]))
    prompt = ("Listen to the audio and answer the multiple-choice question. "
              "Reply with exactly one letter A/B/C/D and nothing else.\n"
              f"Question: {item['question']}\n{choices}\nAnswer:")
    d, wall = call(base, key, Path(item["audio"]), prompt, 20, thinking_budget)
    msg = d["choices"][0]["message"]
    raw = (msg.get("content") or "").strip()
    pred = parse_letter(raw)
    usage = d.get("usage") or {}
    cost = (usage.get("prompt_tokens", 0) * 0.8 + usage.get("completion_tokens", 0) * 2.7) / 1e6
    return {"id": item["id"], "bench": item["bench"], "domain": item["domain"],
            "line": "omni", "answer": item["answer"], "pred": pred,
            "correct": bool(pred == item["answer"]),
            "format_error": pred is None, "raw": raw[:160],
            "thinking_budget": thinking_budget,
            "wall_s": round(wall, 2), "usage": usage, "cost_cny": round(cost, 6)}


def analyze_one(item: dict[str, Any], base: str, key: str,
                thinking_budget: int = 0) -> dict[str, Any]:
    prompt = ("Analyze this audio. Transcribe verbatim in the ORIGINAL language (do not translate). "
              "Return only JSON: {\"segments\":[{\"start\":0.0,\"end\":1.0,\"speaker\":\"S1\",\"text\":\"...\"}],"
              "\"events\":[{\"start\":0.0,\"end\":1.0,\"label\":\"...\"}],"
              "\"music\":{\"present\":true,\"description\":\"...\",\"bpm\":null}}. "
              "Timestamps in seconds with 0.1 precision. Do not invent.")
    d, wall = call(base, key, Path(item["audio"]), prompt, 2200, thinking_budget)
    msg = d["choices"][0]["message"]
    usage = d.get("usage") or {}
    cost = (usage.get("prompt_tokens", 0) * 0.8 + usage.get("completion_tokens", 0) * 2.7) / 1e6
    return {"id": item["id"], "bench": item["bench"], "domain": item["domain"],
            "line": "omni_analyze", "content": (msg.get("content") or "")[:6000],
            "wall_s": round(wall, 2), "usage": usage, "cost_cny": round(cost, 6)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", default=[str(ROOT / "eval/data/mmau_items.jsonl")])
    ap.add_argument("--mode", choices=["answer", "analyze"], default="answer")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--thinking-budget", type=int, default=256)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    items = []
    for p in args.items:
        items += [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        items = items[:args.limit]
    base, key = cfg()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            fn = answer_one if args.mode == "answer" else analyze_one
            futs = {ex.submit(fn, it, base, key, args.thinking_budget): it for it in items}
            for i, fut in enumerate(as_completed(futs), 1):
                r = fut.result()
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{i}/{len(items)}] {r['bench']} {r['id'][:8]} "
                      f"{r.get('pred')} {r.get('correct')} {r['wall_s']}s ¥{r['cost_cny']}", flush=True)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
