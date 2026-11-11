"""Render the human/LLM-readable hearing note from an audio score."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .fuse import display_label
from .media import fmt_ts


def _tag(kind: str) -> str:
    return {"speech": "人声", "event": "事件", "music": "音乐", "silence": "静音"}.get(kind, kind)


def render_hearing(score: dict[str, Any], *, max_rows: int = 120) -> str:
    g = score.get("global") or {}
    views = score.get("views") or {}
    speech = (score.get("speech") or {}).get("segments") or []
    events = score.get("events") or []
    tracks = (score.get("music") or {}).get("tracks") or []
    music = tracks[0] if tracks else None
    rels = score.get("relations") or []
    warnings = score.get("warnings") or []
    caps = score.get("capabilities") or {}
    src = score.get("source") or {}
    mode = caps.get("mode") or g.get("mode") or "basic"

    def overlap(a: int, b: int, c: int, d: int) -> bool:
        return max(a, c) < min(b, d)

    lines: list[str] = []
    lines.append("---")
    lines.append("schema: ear.score/1")
    lines.append(f"mode: {mode}")
    lines.append(f"duration_ms: {int(src.get('duration_ms') or g.get('duration_ms') or 0)}")
    lines.append(f"speakers: {len(g.get('speakers') or []) if isinstance(g.get('speakers'), list) else (g.get('speakers') or 0)}")
    lines.append(f"source: {Path(str(src.get('path') or '')).name if src.get('path') else ''}")
    lines.append("---")
    lines.append("")
    lines.append("# 音频纪要")
    lines.append("")
    lines.append("> " + (views.get("one_line") or g.get("summary") or ""))
    lines.append("")

    # 概览
    dur = int(src.get("duration_ms") or g.get("duration_ms") or 0)
    lines.append("## 概览")
    lines.append("")
    lines.append(f"- 时长：{fmt_ts(dur)}")
    lines.append(f"- 模式：{mode}")
    lines.append(f"- 语音：{len(speech)} 段 / {g.get('speakers') or '未知'} 位说话人")
    if speech:
        prec = "词级" if any(s.get("words") for s in speech) else ("0.5–2s" if mode == "basic" else "分段")
        lines.append(f"- 时间精度：{prec}")
    lines.append(f"- 事件：{len(events)} 个")
    if music:
        lines.append(f"- 音乐：有" + (f"（{music.get('bpm')} BPM）" if music.get("bpm") else ""))
    lines.append(f"- 机器可读：`audio-score.json`；完整上下文：`context.md`")
    lines.append("")

    # 章节
    chapters = views.get("chapters") or []
    if not chapters:
        chapters = [{"start_ms": 0, "end_ms": max(dur, 1), "title": "全片"}]
    lines.append("## 章节")
    lines.append("")
    for ch in chapters[:40]:
        a, b = int(ch["start_ms"]), int(ch["end_ms"])
        title = (ch.get("title") or "").strip()
        lines.append(f"### {fmt_ts(a)}–{fmt_ts(b)} {title}".rstrip())
        lines.append("")
        sp = [s for s in speech if overlap(a, b, int(s["start_ms"]), int(s["end_ms"]))]
        ev = [e for e in events if overlap(a, b, int(e["start_ms"]), int(e["end_ms"]))]
        if sp:
            for seg in sp[:20]:
                txt = (seg.get("text") or "").replace("\n", " ").strip()
                if txt:
                    lines.append(f"- **{fmt_ts(seg['start_ms'])}–{fmt_ts(seg['end_ms'])}** "
                                 f"{seg.get('speaker') or '?'}：{txt}")
            if len(sp) > 20:
                lines.append(f"- … 还有 {len(sp)-20} 段语音")
        if ev:
            for e in ev[:20]:
                lines.append(f"- **事件 {fmt_ts(e['start_ms'])}–{fmt_ts(e['end_ms'])}** "
                             f"{display_label(e)}" + (f"（{e.get('precision')}）" if e.get("precision") else ""))
        if music and overlap(a, b, int(music.get("start_ms", 0)), int(music.get("end_ms", dur))):
            bits = []
            if music.get("bpm"):
                bits.append(f"{music['bpm']} BPM")
            if music.get("description"):
                bits.append(str(music["description"]))
            if music.get("beats_ms"):
                bits.append(f"{len(music['beats_ms'])} beats")
            if bits:
                lines.append("- **音乐**：" + "；".join(bits))
        if not sp and not ev and not music:
            lines.append("- 静音 / 环境声")
        lines.append("")

    # 音乐
    if music:
        lines.append("## 音乐")
        lines.append("")
        if music.get("bpm"):
            lines.append(f"- BPM：{music['bpm']}")
        for k, label in (("genre", "风格"), ("mood", "情绪"), ("vocals", "人声")):
            if music.get(k):
                lines.append(f"- {label}：{music[k]}")
        if music.get("instruments"):
            lines.append("- 乐器：" + "、".join(str(x) for x in music["instruments"]))
        if music.get("description"):
            lines.append(f"- 描述：{music['description']}")
        if music.get("sections"):
            lines.append("- 段落：" + "；".join(
                f"{fmt_ts(x.get('start_ms', 0))}–{fmt_ts(x.get('end_ms', 0))} {x.get('label','')}"
                for x in music["sections"][:20]))
        if music.get("beats_ms"):
            lines.append(f"- 节拍：{len(music['beats_ms'])} beats / {len(music.get('downbeats_ms') or [])} downbeats")
        lines.append("")

    # 事件索引
    lines.append("## 事件索引")
    lines.append("")
    if events:
        for e in events[:60]:
            lines.append(f"- **{fmt_ts(e['start_ms'])}–{fmt_ts(e['end_ms'])}** {display_label(e)}"
                         + (f"（{e.get('precision')}）" if e.get("precision") else ""))
        if len(events) > 60:
            lines.append(f"- … 还有 {len(events)-60} 个，完整见 audio-score.json")
    else:
        lines.append("- 未检测到可命名事件。")
    lines.append("")

    # 可下刀
    if rels or music:
        lines.append("## 可下刀")
        lines.append("")
        n = 0
        for r in rels[:12]:
            lines.append(f"- {fmt_ts(r.get('at_ms', 0))}：{r.get('kind', 'candidate')} "
                         f"{r.get('note', '')}".rstrip())
            n += 1
        if music and music.get("downbeats_ms"):
            for b in music["downbeats_ms"][:6]:
                lines.append(f"- {fmt_ts(int(b))}：downbeat")
                n += 1
        if n == 0:
            lines.append("- 暂无可靠卡点/切点建议。")
        lines.append("")

    lines.append("## 限制")
    lines.append("")
    if warnings:
        for w in warnings[:12]:
            lines.append(f"- {w}")
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 这是给 Agent/人读的层级化摘要；逐段完整数据见 `audio-score.json`，")
    lines.append("> 给文本 LM 的完整上下文见 `context.md`。")
    return "\n".join(lines)

def render_digest(score: dict[str, Any], *, level: int = 1) -> str:
    views = score.get("views") or {}
    g = score.get("global") or {}
    out: list[str] = []
    out.append(views.get("one_line") or g.get("summary") or "")
    if level >= 1:
        out.append("")
        out.append("## 章节")
        for c in (views.get("chapters") or [])[:40]:
            out.append(f"- {fmt_ts(c['start_ms'])}–{fmt_ts(c['end_ms'])}：{c.get('title','')}")
    if level >= 2:
        out.append("")
        out.append("## 时间轴")
        for line in (views.get("timeline_10s") or [])[:200]:
            out.append(f"- {line}")
    return "\n".join(out)
