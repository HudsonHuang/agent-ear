"""Run the Ear benchmark: no-audio baseline vs Ear+text-LLM.

Usage:
  python eval/run_eval.py --items eval/data/mmau_items.jsonl --line no_audio --limit 5
  python eval/run_eval.py --items eval/data/mmau_items.jsonl --line ear --limit 5
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from eval.note import build_note  # noqa: E402
from ear.context import build_context  # noqa: E402
DEFAULT_ITEMS = [ROOT / "eval/data/mmau_items.jsonl", ROOT / "eval/data/cmdar_items.jsonl"]
LETTERS = "ABCD"


def load_items(paths: list[Path], limit: int | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(json.loads(line))
    if limit:
        items = items[:limit]
    return items


def llm_config() -> tuple[str, str, str]:
    base = (os.environ.get("EVAL_LLM_BASE_URL") or "").rstrip("/")
    key = os.environ.get("EVAL_LLM_API_KEY") or ""
    model = os.environ.get("EVAL_LLM_MODEL") or "qwen-plus"
    if not base or not key:
        cfg_path = Path.home() / ".bailian" / "config.json"
        if cfg_path.is_file():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            base = base or (str(cfg.get("base_url") or "").rstrip("/") + "/compatible-mode/v1")
            key = key or str(cfg.get("api_key") or "")
    if not base or not key:
        raise SystemExit("No text LLM credentials; set EVAL_LLM_BASE_URL/KEY or ~/.bailian/config.json")
    return base, key, model


def call_llm(base: str, key: str, model: str, system: str, user: str) -> str:
    r = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": 8,
        },
        timeout=120,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"LLM {r.status_code}: {r.text[:300]}")
    return (r.json()["choices"][0]["message"].get("content") or "").strip()


def parse_letter(text: str) -> str | None:
    m = re.search(r"\b([ABCD])\b", text.upper())
    return m.group(1) if m else None


def ensure_ear(item: dict[str, Any], cache_root: Path, mode: str = "ear",
               need: str = "transcript,events,beat") -> tuple[dict[str, Any], float]:
    bench = item["bench"]
    out = cache_root / ("" if mode == "ear" else mode) / bench / item["id"]
    score_p = out / "audio-score.json"
    if score_p.is_file():
        return json.loads(score_p.read_text(encoding="utf-8")), 0.0
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["EAR_LABEL_LANG"] = "en" if bench.startswith("mmau") else "zh"
    cmd = [sys.executable, "-m", "ear.cli", "listen", item["audio"],
           "--out", str(out), "--force"]
    if mode == "ear":
        cmd += ["--aed", "auto"]
    else:
        cmd += ["--mode", mode]
        if mode == "precise":
            cmd += ["--need", need]
    if bench == "cmdar":
        cmd += ["--language", "zh"]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=420)
    if p.returncode != 0 or not score_p.is_file():
        raise RuntimeError(f"ear failed: {p.stderr[-600:] or p.stdout[-600:]}")
    return json.loads(score_p.read_text(encoding="utf-8")), time.time() - t0


def prompt_for(item: dict[str, Any], note: str | None) -> tuple[str, str]:
    choices = "\n".join(f"{LETTERS[i]}. {c}" for i, c in enumerate(item["choices"]))
    system = ("Answer the multiple-choice question. Pick the single best option and reply with "
              "exactly one letter A/B/C/D.")
    if note:
        system += (" A hearing note from an audio analysis system is provided. Use it as evidence "
                   "when relevant, but ignore it if it does not help.")
        user = f"Hearing note:\n{note}\n\nQuestion: {item['question']}\n{choices}\n\nAnswer:"
    else:
        user = f"Question: {item['question']}\n{choices}\n\nAnswer:"
    return system, user


def run_one(item: dict[str, Any], line: str, cache_root: Path,
            llm: tuple[str, str, str], note_mode: str = "qa",
            need: str = "transcript,events,beat") -> dict[str, Any]:
    base, key, model = llm
    note = None
    ear_s = 0.0
    err = None
    try:
        if line in ("ear", "basic", "precise"):
            score, ear_s = ensure_ear(item, cache_root, mode=line, need=need)
            if note_mode == "hearing":
                note = (cache_root / ("" if line == "ear" else line) / item["bench"] / item["id"] / "hearing.md").read_text(encoding="utf-8")
            elif note_mode == "context":
                note = build_context(score, max_chars=12000,
                                     lang="en" if item["bench"].startswith("mmau") else "zh")
            else:
                lang = "en" if item["bench"].startswith("mmau") else "zh"
                note = build_note(score, item["question"], lang=lang)
            note = note[:6000]
        system, user = prompt_for(item, note)
        raw = call_llm(base, key, model, system, user)
        pred = parse_letter(raw)
        fmt_err = pred is None
    except Exception as exc:
        raw, pred, fmt_err = "", None, True
        err = f"{type(exc).__name__}: {str(exc)[:300]}"
    return {
        "id": item["id"], "bench": item["bench"], "domain": item["domain"],
        "line": line, "answer": item["answer"], "pred": pred,
        "correct": bool(pred == item["answer"]), "format_error": fmt_err,
        "raw": raw[:120], "note_chars": len(note or ""), "ear_s": round(ear_s, 2),
        "error": err,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", default=[str(p) for p in DEFAULT_ITEMS])
    ap.add_argument("--line", choices=["no_audio", "ear", "basic", "precise"], required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache", default=str(ROOT / "eval/cache"))
    ap.add_argument("--note-mode", choices=["qa", "hearing", "context"], default="qa")
    ap.add_argument("--need", default="transcript,events,beat")
    args = ap.parse_args()

    items = load_items([Path(p) for p in args.items], args.limit)
    llm = llm_config()
    out = Path(args.out) if args.out else ROOT / "eval/results" / f"{args.line}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    done = 0
    with out.open("w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(run_one, it, args.line, Path(args.cache), llm,
                              args.note_mode, args.need): it for it in items}
            for fut in as_completed(futs):
                res = fut.result()
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
                f.flush()
                done += 1
                print(f"[{done}/{len(items)}] {res['bench']} {res['id'][:8]} "
                      f"{'OK' if res['correct'] else 'x'} {res['pred']} / {res['answer']} "
                      f"{res['ear_s']}s", flush=True)
    print(f"wrote {out} in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
