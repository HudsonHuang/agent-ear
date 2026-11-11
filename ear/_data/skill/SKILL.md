---
name: agent-ear
description: >-
  Give text-only agents an ear for offline audio/video: turn speech, sound events,
  and music into one timestamped audio-score.json plus a hierarchical hearing.md.
  Use when the user provides an audio/video file or asks to transcribe with timestamps,
  find laughter/applause/sounds, cut to the beat, make SDH subtitles, or describe
  what happens in a clip. Do not use for live translation/realtime streams, spatial
  acoustics, voiceprint identity, or a complete musical score.
---

# agent-ear：给文本 Agent 一副离线耳朵

> **强依赖：Qwen Omni API。** basic/ask/precise/music 都依赖 `qwen3.8-omni-flash`；没有 Key/网络时只有 `privacy` 本地降级可用。precise 还依赖 Qwen ASR。

`agent-ear` 把一段**离线**音频/视频编译成：

- `audio-score.json`：同一时钟上的语音、事件、音乐、关系、置信度；
- `hearing.md`：层级化、带时间戳的 Markdown 纪要；
- `context.md`：给文本 LM 的完整上下文。

## 先确认安装

在运行分析前，先执行本 Skill 目录里的 wrapper：

```bash
# macOS / Linux
./scripts/agent-ear doctor --json

# Windows
scripts\agent-ear.cmd doctor --json
```

如果返回 `key configured: false` / `Qwen API key is not configured`：

1. **不要向用户索要 API Key，也不要在聊天里粘贴 Key。**
2. 让用户在**终端**运行：
   ```bash
   agent-ear setup
   ```
3. 用户完成后重新运行 doctor。

安装/修复：

```bash
agent-ear setup                 # 交互式：Qwen Key + 选择 Codex/DSH/Claude
agent-ear doctor                # 依赖/配置/Skill 检查
agent-ear setup --target codex  # 只装 Codex Skill
```

`agent-ear setup` 会把音频发送到阿里云 Qwen 的隐私/费用提示说清楚；
`privacy` 模式不调用任何 API。

## 三种运行方式

### 1. 直接问答（单问题最快）

```bash
./scripts/agent-ear ask input.mp4 "这段音频里发生了什么？"
```

一次 Omni 调用同时返回完整分析 + 答案。适合“只问一次”。

### 2. 详细转录（默认，basic）

```bash
./scripts/agent-ear listen input.mp4 --mode basic --out .ear/my-video
```

- 输出完整 transcript/events/music + 层级 `hearing.md` + `context.md`；
- 时间戳 0.5–2s，能粗剪，不能精确打轴；
- 之后可以让文本 LM 基于 `context.md` 连续问，不重复调 Omni：
  ```bash
  ./scripts/agent-ear ask --score .ear/my-video "谁在什么时候笑了？"
  ```

### 3. 精确模式（precise）

```bash
./scripts/agent-ear listen input.mp4 --mode precise --need transcript,events,beat --out .ear/my-video-precise
```

- Omni 负责召回；Qwen ASR 补词级时间；BEATs 补 40ms 事件；Beat This! 补 beat；
- `--need` 不指定的能力不会跑；
- 事件 refine 只修 Omni 已提名的事件，不做全量开放检测。

### 按需求只跑需要的层（长视频推荐）

```bash
# 只要笑声：不转写，只找 Laughter
./scripts/agent-ear listen long.mp4 --mode basic --request "把视频里所有笑声都剪出来"
./scripts/agent-ear listen long.mp4 --mode precise --request "把视频里所有笑声都剪出来"

# 只要卡点：不跑 ASR
./scripts/agent-ear listen long.mp4 --mode precise --request "按节拍卡点"
```

`--request` 会把自然语言映射为 intent/labels/needs，并写进 `audio-score.intent`。
没有具体需求时**不要**用 targeted；默认 basic 详细转录，避免漏掉用户没说的内容。

## 输出怎么读

```text
.ear/<name>-<hash>/
├── audio-score.json       # 完整契约（schema/audio-score.schema.json）
├── audio-score.json.gz
├── hearing.md             # 层级 Markdown：概览 / 章节 / 音乐 / 事件索引 / 限制
├── digest.md              # 章节级短摘要
├── context.md             # 给文本 LM 的完整上下文
└── work/                  # 16k/32k wav
```

- `hearing.md` 是给人/Agent 读的派生视图；JSON 是唯一事实源。
- 事件 `precision`：`omni-coarse`（0.5–2s）或 `refined-40ms`。
- 不要忽略 `warnings[]`：缺 key、ASR 失败、模型缺失、短音频说话人塌陷都会写在这里。

## 边界

能用：离线文件、剪辑前置分析、找高光、卡点、SDH 字幕、配音 QA、媒体自检。

不要用：

- Live Translation、实时通话、实时理解、直播；
- 空间声学/空间定位/多轨空间；
- 完整音乐总谱/出版级谱；
- 声纹身份/情绪诊断/deepfake 检测。

## 安装时检查 AED 更新

AED 选型不是永久的：

1. 读 `agent-ear doctor --json` 里的 `aed.last_reviewed`；
2. 超过 6 个月，查是否有更新的 frame-level AED（40ms 级、AudioSet Strong 447+ 类、MIT/Apache）；
3. 新 provider 先用 `--aed <id>` 跑小集对比，不要静默改默认；
4. 更新 `ear/aed_registry.py` 的 `LAST_REVIEWED` 与文档。

## 参考

- `references/output-schema.md`
- `references/request-strategies.md`
- `references/direct-vs-transcribe.md`
- `agent-ear doctor --json`
