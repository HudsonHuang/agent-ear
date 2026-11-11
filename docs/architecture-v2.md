# Ear v2 架构：Omni 前置 + 按需精确

> 依据：第一轮水位（2026-11-11）显示，Omni 单模型在 QA 上 87.2%（thinking 256）vs Ear 管线 58.9%；但 Omni 的 ASR/事件时间戳是 0.5s / 1–2s 级，不能做精确打轴与卡点。
>
> 结论：**基础理解用 Omni；精确时间用本地模型按需补；整个 Skill 由用户意图驱动，不再固定跑全套。**

## 1. 一句话架构

```text
音频/视频
  └─ Stage 0: Omni 前置（必跑，除 privacy）
       ├─ 语义：讲了什么、谁在说、有什么声音、音乐风格/乐器/段落
       ├─ 粗时间：transcript 段、事件区间、speech/music 存在性
       └─ 路由信号：has_speech / has_music / has_events / language
  └─ Intent Router（按用户需求决定要不要继续）
       ├─ describe / ask        → 停，直接回答
       ├─ transcribe / subtitle → 有 speech 才跑 Qwen ASR（词级时间）
       ├─ beat / cut            → 跑 Beat This!，不跑 ASR
       ├─ event-precise         → 只对 Omni 事件窗口跑 BEATs 修时间
       ├─ music                 → Omni + Beat This!（BPM/beats）；段落可选
       └─ privacy               → 不跑 Omni；MOSS + BEATs + Beat This!
  └─ Fusion
       ├─ Omni 保召回；本地模型保精度
       ├─ 事件：Omni 给 label/区间，BEATs 只在窗口内 refine onset/offset
       └─ 语音：Omni 给文本/语种，Qwen ASR 只在需要词级时间时补
  └─ audio-score + hearing.md + digest
```

## 1.5 直接 ask vs 转录后 ask

- 40 条子集：直接 ask 87.5%；一次调用“详细转录 + 回答” **90.0%**；转录后强文本 77.5%；普通文本 65%；压缩 note 55%。
- 差别集中在 sound/music；speech 转录+强文本可反超。详见 [direct-vs-transcribe.md](direct-vs-transcribe.md)。

## 2. 为什么这样级联

### 2.0 basic 有两个面

- **`agent-ear listen --mode basic`（主形态）**：一次 Omni 调用 → 完整 transcript/events/music → `audio-score.json` + 层级 `hearing.md` + `context.md`。它是**详细转录/描述模式**，0.5–2s 时间戳，能支持粗剪/摘要；下游文本 LM 直接用 `context.md` 问多个问题，不再调 Omni。富上下文 + qwen3.8-max 在 40 条子集上 77.5%（qwen-plus 65.0%）。
- **`agent-ear ask`（可选）**：音频 + 问题直接给 Omni，一次返回完整分析 + 答案，适合一次性问答（87.2%）；不是 basic 的唯一/核心入口。

### 2.1 Omni 的强项与弱项

| 能力 | Omni | Ear 本地层 |
|---|---|---|
| 语义理解/联合推理 | **强**（87.2% QA） | 弱（58.9%） |
| 事件召回 | **强**（能说出笑声/掌声/音乐/对话） | 弱（AudioSet 标签泛化） |
| 事件时间精度 | 1–2s 级 | **40ms**（BEATs） |
| ASR 文本 | 可用（CER ~16%） | **更准**（Qwen ASR） |
| 词级时间 | 0.5s 级 | **词级**（Qwen） |
| 节拍/卡点 | 无 beat grid | **Beat This!** |
| 成本/速度 | **¥0.034/h（0）/ ¥0.141/h（256），2.5–5.7s/短条** | Qwen ASR + 本地计算 |

所以正确的分工是：**Omni 决定“有什么”，本地模型决定“精确在哪”。**

### 2.2 事件级联：只在 Omni 给的窗口里修时间

```text
Omni event: {label: "laughter", start: 12.0, end: 14.0, conf: 0.9}
  → 映射到 BEATs/AudioSet 类（Laughter）
  → 在 [10.5, 15.5] 窗口跑 BEATs（40ms）
  → 找该类的 frame-level 峰值/连续段
  → 如果置信度足够：更新 start/end，precision="refined-40ms"
  → 否则保留 Omni 区间，precision="omni-coarse"
```

好处：

- **AED 的误召回不再是问题**：只在 Omni 事件窗口内找，窗口外不报。
- **AED 的漏召回也不致命**：找不到就保留 Omni 的粗时间。
- **成本低**：BEATs 只跑几秒窗口，不是整段音频。
- **可解释**：每个事件有 `omni_interval` + `refined_interval` + `precision`。

### 2.3 语音级联：Omni 说没有文本，就不跑 ASR

```text
Omni transcript:
  - 有文本 → 若用户要字幕/词级时间，跑 Qwen ASR（整段或语音区）
  - 无文本 → 跳过 ASR（用户明确不需要“无中生有”）
  - 只有纯文本需求 → 直接用 Omni 文本，不跑 Qwen
```

- Omni 文本可作为 Qwen ASR 的先验/校验；两者都保留 `source`。
- 若用户只要“讲了什么”，不跑 Qwen ASR。
- 若用户要“字幕/逐字稿/打轴”，才跑 Qwen ASR。

### 2.4 节拍级联：只要卡点，不跑 ASR

```text
用户说“卡点/踩点/按节拍剪”
  → Omni 判 has_music
  → 只跑 Beat This!（BPM/beats/downbeats）
  → 不跑 ASR、不跑 BEATs
```

## 3. Intent Router

| 用户意图 | Omni | Qwen ASR | BEATs | Beat This! | 输出 |
|---|---|---|---|---|---|
| “这段讲了什么/为什么好笑” | 必跑 | 否 | 否 | 否 | 文本回答 + 摘要 |
| “字幕/逐字稿/打轴” | 必跑 | 有 speech 才跑 | 否 | 否 | 词级 transcript + SRT |
| “卡点/踩点/按节拍剪” | 必跑 | 否 | 否 | 必跑 | BPM + beats + cut_candidate |
| “精确找笑声/掌声/玻璃碎” | 必跑 | 否 | 窗口 refine | 可选 | 40ms 事件区间 |
| “音乐风格/乐器/段落” | 必跑 | 否 | 可选 | 可选 | 音乐描述 + BPM + sections |
| “隐私/本地/不要上传” | 否 | MOSS | 必跑 | 可选 | 本地 score |

**判定方式**：

1. 显式参数优先（`--need subtitle|beat|event|music|privacy`）。
2. 否则从用户话术推断（关键词表）。
3. 推断结果写入 `provenance.intent`，让用户知道跑了什么。

## 4. 输出 schema 的变化

两种形态（详细 JSON + 层级 Markdown）见 [output-schema.md](output-schema.md)。

在现有 `audio-score` 上增加：

```json
{
  "capabilities": {
    "omni": "qwen3.8-omni-flash",
    "asr": "qwen-audio-3.1-filetrans | null",
    "aed": "pretrainedsed-beats-strong | null",
    "beat": "beat_this-small0 | null",
    "mode": "basic | precise | privacy"
  },
  "intent": {
    "requested": ["describe", "event_precise"],
    "skipped": ["asr", "beat"]
  },
  "events": [
    {
      "label": "Laughter",
      "start_ms": 12120,
      "end_ms": 13980,
      "precision": "refined-40ms",
      "omni_interval_ms": [12000, 14000],
      "refined_by": "beats-strong",
      "conf": 0.82,
      "salience": 0.91
    }
  ],
  "speech": {
    "segments": [
      {
        "text": "...",
        "source": "qwen-asr | omni",
        "words": []
      }
    ]
  }
}
```

- `precision`: `omni-coarse` / `refined-40ms` / `word-level`.
- `omni_interval_ms`: 保留原始 Omni 区间，便于审计。
- `intent.skipped`: 明确哪些能力没跑，避免把“没跑”当“没有”。

## 5. 代码结构简化

当前 `ear/` 是平铺模块；建议：

```text
ear/
  providers/
    omni.py          # Qwen3.8-Omni-Flash：分析/回答，返回结构化 JSON
    asr_qwen.py      # Qwen ASR（词级）
    aed_beats.py     # PretrainedSED BEATs（40ms）
    beats.py         # Beat This!
    moss.py          # privacy 模式（Roadmap）
  routing.py         # intent -> capabilities
  fusion.py          # Omni 粗 + 本地精
  render.py          # hearing.md / digest
  cli.py
```

原则：

- **Provider 只做一件事**，不互相 import。
- **Router 决定跑谁**，不把“全跑”写死。
- **Fusion 只做归一化/合并**，不调模型。
- **Render 只读 score**，不调模型。

## 6. 音乐模式：Omni 先，转谱后置

### 6.1 Omni 音乐质量（实测 3 条 30s 片段）

- 能输出：genre / mood / BPM / key / instruments / vocals / sections / notable events。
- 例：
  - “Lo-fi hip hop / spoken word / ambient；95 BPM；E minor；plucked strings + synth pad + male spoken vocal”
  - “Indie Soul / Lo-fi R&B；126 BPM；D Minor；Electric Guitar / Bass / Drums”
  - “Mandopop Ballad；65 BPM；G Major；Acoustic Guitar”
- 判断：
  - **风格/情绪/乐器/人声/section 有可用性**（粗粒度）。
  - **BPM/key 可能不准**；不能替代 Beat This! / 调性分析。
  - **没有和弦/转谱/精确 section 边界**；复杂和声题（如 069383b9）答不了。

### 6.2 要不要加转谱

**暂时不加。**

- 开源转谱：basic-pitch（单音/钢琴/旋律，instrument-agnostic 但精度有限）、MT3/YourMT3（多乐器，重、类别有限、GPL/部署坑）；full-mix 多轨 MIDI 仍不可靠。
- 付费 API：Mirelo（full-mix per-instrument MIDI）、Klangio（单乐器）；可做 `--music-transcribe api` 可选，不进默认。
- 因此音乐模式 = **Omni 描述 + Beat This! BPM/beats + 可选 All-In-One sections + 歌词**；转谱作为可选付费/本地增强，不承诺。

## 7. 成本模型

| 模式 | 调用 | 成本/音频小时 | 延迟 |
|---|---|---:|---:|
| basic（Omni thinking 0） | Omni answer | **¥0.034** | 2.5s/短条 |
| basic（Omni thinking 256） | Omni answer | **¥0.141**（短条）/ **¥0.211**（1h 结构化） | 5.7s/短条；1h 231s |
| subtitle | Omni + Qwen ASR | ~¥0.10 | +Qwen ASR |
| beat/cut | Omni + Beat This! | ~¥0.034 | +本地秒级 |
| event-precise | Omni + BEATs 窗口 | ~¥0.034 | +窗口 BEATs |
| music | Omni + Beat This! | ~¥0.034 | +本地 |
| privacy | MOSS + BEATs + Beat This! | 0 API | 本地慢 |

## 8. 已完成的 refine 评测

- 34 个 Omni 事件被 BEATs 40ms 修正；start 位移 median **+1.52s**，end median **-20ms**；详见 [refine-eval.md](refine-eval.md)。
- 目前只有 Laughter 这类可映射标签被 refine；开放标签（bird chirping/spray hiss）仍是 `omni-coarse`。

## 9. 评估下一轮

1. **Omni thinking 256 全量 180**：已验证 87.2%（thinking 0 为 81.7%）；下一步测 1 小时长音频的 RTF/成本。
2. **事件 refine 评测**：20 条人工标注 onset/offset，比较 `omni-coarse` vs `refined-40ms` 的误差。
3. **意图路由测试**：10 条用户请求，检查是否只跑需要的后端。
4. **音乐难度**：补 30 条有和弦/乐器/section 标注的音乐片段；否则音乐水位会虚高。
5. **中文加难**：CMDAR 97.5% 已饱和，补 open-ended / 方言 / 长音频。

## 9. 一句话

**Omni 负责“听懂”，本地模型负责“对准”；Skill 负责“按需调用、融合、给出可审计的时间轴”。**
