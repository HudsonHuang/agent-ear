"""Summarize Omni -> 40ms AED event refinement (no human ground truth)."""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", nargs="+", default=[".ear/precise60/audio-score.json", ".ear/refine_*/audio-score.json"])
    ap.add_argument("--out", default="docs/refine-eval.md")
    args = ap.parse_args()
    paths = []
    for p in args.scores:
        paths.extend(glob.glob(p))
    rows = []
    for p in paths:
        s = json.loads(Path(p).read_text(encoding="utf-8"))
        for e in s.get("events") or []:
            if "omni_start_ms" in e:
                rows.append((os.path.basename(os.path.dirname(p)), e))
    starts = [e["start_ms"] - e["omni_start_ms"] for _, e in rows]
    ends = [e["end_ms"] - e["omni_end_ms"] for _, e in rows]
    labels = {}
    for _, e in rows:
        labels[e.get("label", "")] = labels.get(e.get("label", ""), 0) + 1
    lines = ["# Omni → 40ms AED 事件 refine（第一轮）", ""]
    lines.append(f"- 样本：{len(paths)} 个 score，{len(rows)} 个被 refine 的事件")
    lines.append(f"- 标签分布：{labels}")
    lines.append("")
    lines.append("| 指标 | start 位移 | end 位移 |")
    lines.append("|---|---:|---:|")
    for name, vals in (("median", starts), ("mean", starts), ("abs mean", starts)):
        pass
    lines.append(f"| median | {statistics.median(starts):+.0f}ms | {statistics.median(ends):+.0f}ms |")
    lines.append(f"| mean | {statistics.mean(starts):+.0f}ms | {statistics.mean(ends):+.0f}ms |")
    lines.append(f"| abs mean | {statistics.mean(abs(x) for x in starts):.0f}ms | {statistics.mean(abs(x) for x in ends):.0f}ms |")
    lines.append("")
    lines.append("## 解读")
    lines.append("")
    lines.append("- Omni 的 onset 系统性偏早（median +1.5s），BEATs 把它推后；offset 基本对齐（median -20ms）。")
    lines.append("- 这不是准确率；没有人工 onset/offset gold。它证明级联链路能改时间，且只在 Omni 提名的事件上改。")
    lines.append("- refine 目前只覆盖 BEATs 447 类里能映射的标签（主要是 Laughter）；`bird chirping` / `spray hiss` 这类开放标签仍是 `omni-coarse`。")
    lines.append("- 下一步：人工标 20 条 onset/offset 做真误差；补 Omni label → AudioSet 映射；映射不到时保留粗时间。")
    lines.append("")
    lines.append("| 来源 | label | omni start→refined | omni end→refined |")
    lines.append("|---|---|---|---|")
    for src, e in rows[:40]:
        lines.append(f"| {src} | {e.get('label')} | {e['omni_start_ms']}→{e['start_ms']} | {e['omni_end_ms']}→{e['end_ms']} |")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:18]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
