"""Summarize eval result JSONL files."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load(paths: list[Path]) -> list[dict]:
    out = []
    for p in paths:
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def acc(rows: list[dict]) -> tuple[float, int]:
    n = len(rows)
    if not n:
        return 0.0, 0
    return sum(1 for r in rows if r.get("correct")) / n, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", default=["eval/results/no_audio.jsonl", "eval/results/ear.jsonl"])
    ap.add_argument("--out", default="eval/results/report.md")
    args = ap.parse_args()
    rows = load([Path(p) for p in args.results])
    lines = ["# Ear 水位评估（第一轮）", ""]
    lines.append("| line | bench | domain | n | acc |")
    lines.append("|---|---|---:|---:|---:|")
    groups = defaultdict(list)
    for r in rows:
        groups[(r["line"], r["bench"], r["domain"])].append(r)
    for key in sorted(groups):
        a, n = acc(groups[key])
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {n} | {a*100:.1f}% |")
    # overall
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| line | n | acc | format_error |")
    lines.append("|---|---:|---:|---:|")
    for line in sorted({r["line"] for r in rows}):
        sub = [r for r in rows if r["line"] == line]
        a, n = acc(sub)
        fe = sum(1 for r in sub if r.get("format_error"))
        lines.append(f"| {line} | {n} | {a*100:.1f}% | {fe} |")
    # paired delta
    by = {(r["line"], r["bench"], r["id"]): r for r in rows}
    pairs = []
    for (line, bench, rid), r in by.items():
        if line != "ear":
            continue
        base = by.get(("no_audio", bench, rid))
        if base:
            pairs.append((bench, rid, int(base["correct"]), int(r["correct"])))
    if pairs:
        lines.append("")
        lines.append("## Ear - no_audio（配对）")
        lines.append("")
        lines.append("| bench | n | no_audio | ear | delta |")
        lines.append("|---|---:|---:|---:|---:|")
        for bench in sorted({p[0] for p in pairs}):
            sub = [p for p in pairs if p[0] == bench]
            na = sum(p[2] for p in sub) / len(sub) * 100
            ea = sum(p[3] for p in sub) / len(sub) * 100
            lines.append(f"| {bench} | {len(sub)} | {na:.1f}% | {ea:.1f}% | {ea-na:+.1f}pp |")
        na = sum(p[2] for p in pairs) / len(pairs) * 100
        ea = sum(p[3] for p in pairs) / len(pairs) * 100
        lines.append(f"| **all** | {len(pairs)} | {na:.1f}% | {ea:.1f}% | **{ea-na:+.1f}pp** |")
    # latency
    ear = [r for r in rows if r["line"] == "ear"]
    if ear:
        lines.append("")
        lines.append("## 延迟")
        lines.append("")
        vals = sorted(r.get("ear_s", 0) for r in ear)
        avg = sum(vals) / len(vals)
        p50 = vals[len(vals) // 2]
        p90 = vals[min(len(vals) - 1, int(len(vals) * 0.9))]
        lines.append(f"- Ear 处理（含 ASR/AED/融合）：avg {avg:.1f}s, p50 {p50:.1f}s, p90 {p90:.1f}s")
        lines.append(f"- 平均 note 字符数：{sum(r.get('note_chars',0) for r in ear)/len(ear):.0f}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
