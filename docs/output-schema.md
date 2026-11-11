# Ear 输出 Schema：两种形态

Ear 的产物分两层，**同一份时间事实**，两种消费方式：

1. **详细 JSON**：`audio-score.json`（机器可读、可程序化、可审计）
2. **层级化 Markdown**：`hearing.md`（Agent/人读），以及 `context.md`（给文本 LM 的完整上下文）

> `hearing.md` 是 `audio-score.json` 的**派生视图**，不是第二份事实源。JSON 是唯一事实源。

## 1. JSON：`audio-score.json`

Schema：`schema/audio-score.schema.json`，当前 `schema: "ear.score/1"`。

### 顶层

当前 schema 已收口：顶层与核心对象都 `additionalProperties: false`；`global.top_sounds` 同时兼容 Omni 的 event 对象和本地 AED 的 `{label, score}` 标签对象。Golden examples：`schema/examples/{basic,precise,events}.json`。

```json
{
  "schema": "ear.score/1",
  "source": {"path": "...", "sha256": "...", "duration_ms": 60000, "fps": null},
  "capabilities": {
    "omni": "qwen3.8-omni-flash",
    "speech": "omni | qwen-asr | null",
    "events": "omni | omni+refined | null",
    "music": "omni | beat_this-small0 | null",
    "aed": "pretrainedsed-beats-strong",
    "vad": "silero-vad",
    "mode": "basic | precise | music | privacy"
  },
  "intent": {"requested": ["transcript", "events"], "skipped": ["beat"]},
  "global": {"summary": "...", "speakers": 2, "speech_ratio": 0.8, "music_ratio": 0.2,
             "duration_ms": 60000, "mode": "basic", "top_sounds": []},
  "speech": {"segments": [], "turns": [], "omni_transcript": []},
  "music": {"tracks": []},
  "events": [],
  "relations": [],
  "timeline": [],
  "views": {"one_line": "...", "chapters": [], "timeline_10s": []},
  "warnings": [],
  "provenance": {"tool_version": "0.2.0", "elapsed_s": 16.5,
                 "omni": {"usage": {}, "wall_s": 16.1, "chunks": 1,
                          "profile": "full", "targets": []},
                 "probe": {}}
}
```

### 关键约定

- **唯一时钟**：所有时间都是 `start_ms` / `end_ms`，整数毫秒，`[start,end)`。
- **事件精度**：`events[].precision`
  - `omni-coarse`：Omni 时间（0.5–2s 级）
  - `refined-40ms`：BEATs 窗口/对齐后的 40ms 级
  - 保留 `omni_start_ms` / `omni_end_ms` 便于审计
- **语音精度**：
  - Omni 段：`source="omni"`，无 `words`
  - Qwen ASR：`source="qwen-asr"`，有 `words`
- **说话人**：`speaker` 是匿名 ID（`S1`/`S2`/Qwen `S0`）；`global.speakers` 是数量。
- **音乐**：`music.tracks[]` 至少含 `bpm`、`beats_ms`、`downbeats_ms`、`quality`、`description`；Omni 只有描述/BPM，Beat This! 补 beat grid。
- **能力声明**：`capabilities` 说明哪些层跑了；`intent.skipped` 说明哪些**没跑**，避免把“没跑”当“没有”。
- **扩展**：新增字段必须向后兼容；破坏性变更才升 `schema` major。

## 2. Markdown：`hearing.md`

给 Agent/人读的层级化时间描述。稳定 heading 契约：

```markdown
---
schema: ear.score/1
mode: basic
duration_ms: 60000
speakers: 2
source: input.mp4
---

# 音频纪要

> 一句话摘要

## 概览
- 时长 / 模式 / 语音段数 / 时间精度 / 事件数 / 音乐
- 机器可读：audio-score.json；完整上下文：context.md

## 章节
### 00:00–01:00 章节标题
- **00:00–00:01** S1：...
- **事件 00:07–00:10** 笑声（omni-coarse）
- **音乐**：140 BPM；...

## 音乐
- BPM / 风格 / 情绪 / 器乐 / 描述 / section / beats

## 事件索引
- **00:07–00:10** 笑声（omni-coarse）

## 可下刀
- 00:01.60：downbeat
- 00:02.40：speech/event boundary

## 限制
- Omni timestamps are coarse...
```

规则：

- 每章用 `### HH:MM–HH:MM 标题`；章内用 bullet，不用大表。
- 每个 bullet 以粗体时间开头，Agent 可直接解析。
- 事件用 `**事件 start–end** label（precision）`。
- 音乐段用 `**音乐**` bullet。
- 长音频最多 40 章、每章最多 20 段语音/事件；完整数据在 JSON / `context.md`。
- `hearing.md` 不追求全量，追求**可扫读、可引用、可下刀**。

## 3. `context.md`

给文本 LM 的完整上下文（不是给人看的排版）：

```text
SUMMARY: ...
TRANSCRIPT:
[00:00.00-00:01.00] S1: ...
EVENTS:
[00:07.00-00:10.00] Laughter (precision=omni-coarse)
MUSIC: 140 BPM; ...
CAVEATS:
- ...
```

- 默认 `max_chars=12000`；超出截断。
- `agent-ear ask --score <dir> "问题"` 直接用它问文本 LM，**不再调用 Omni**。
- 适合“一次 Omni，多个问题”。

## 4. 模式如何改 Schema

| 模式 | JSON 变化 | Markdown 变化 |
|---|---|---|
| `basic` | `speech.segments` 来自 Omni；`events[].precision=omni-coarse`；`music` 描述 | 章节 + 全量转写（前 120 段）+ 事件索引 |
| `precise` | `speech` 换成 Qwen 词级；`events` 部分 `refined-40ms`；`music` 加 beat grid | 概览标“词级”；事件标 `refined-40ms`；可下刀更密 |
| `music` | `music.tracks` 增加 BPM/beats/description；可选 sections | `## 音乐` 展开；章节里标音乐段 |
| `privacy` | 无 Omni；本地 ASR/AED/beat | 同 basic，但 `capabilities` 标明本地 |

## 5. 版本与测试

- Schema 文件：`schema/audio-score.schema.json`；所有输出用 `jsonschema.validate` 校验。
- 测试：`tests/test_schema.py`、`tests/test_render.py`、`tests/test_score.py`。
- 新增 provider：返回 `events[]` / `segments[]` / `music.tracks[]` 同一形状；`precision` 必须声明。
