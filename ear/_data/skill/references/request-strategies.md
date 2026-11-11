# 按请求动态选策略

> 默认：用户没提具体需求 → **详细转录**（full profile），质量优先。  
> 用户提了具体需求 → 只跑需要的层；同一个 basic/precise，执行计划会变。

## 1. 请求 → 计划

| 用户说 | intent | Omni profile | 语音 | 事件 | 节拍 | 输出 |
|---|---|---|---|---|---|---|
| “详细记录/转录一下” | transcribe | full | 全量 | 全量 | 可选 | 完整 JSON + Markdown |
| “把笑声都剪出来” | events | **events（Laughter）** | **不转写** | 只找笑声 | 不跑 | 笑声时间轴 + cut candidates |
| “把掌声/玻璃碎/狗叫找出来” | events | events(labels) | 不转写 | 目标事件 | 不跑 | 目标事件时间轴 |
| “按节拍卡点” | beat | events? / full | 不跑 | 不跑 | Beat This! | BPM/beats/cut |
| “加字幕/逐字稿” | transcribe | full | Qwen ASR 词级 | 可选 | 不跑 | 词级 transcript |
| “音乐风格/乐器/段落” | music | full | 不跑 | 不跑 | Beat This! | 音乐层 + BPM/beats |
| “隐私/本地” | privacy | 无 Omni | 本地 | BEATs | Beat This! | 本地 score |
| “这段为什么好笑” | qa | 直接 ask（音频+题） | — | — | — | 答案；需要时再 full |

## 2. 长视频：只找笑声

用户上传 3 小时视频，说“把笑声都剪出来”：

```text
basic:
  Omni events profile，120s 分块，2s overlap
  → 只返回 laughter events（无 transcript）
  → 合并边界重复、去重
  → audio-score + hearing.md（笑声索引）

precise:
  同一份 Omni laughter events
  → BEATs 40ms refine（只修这些事件；不跑 Qwen ASR）
  → 输出 refined-40ms 的笑声区间 + cut candidates
```

**5 分钟样本实测**：

| 策略 | 耗时 | 事件数 | refine |
|---|---:|---:|---:|
| 详细转录 basic | 68.5s | — | — |
| 只要笑声 basic | **15.2s** | 66 | 0 |
| 只要笑声 precise | **24.1s** | 65 | 53/65 |

好处：

- 不转写 3 小时语音，省 ASR 成本/时间；
- 不跑全量 AED 开放检测，只对齐 Omni 提名的笑声；
- 基础模式能给出粗时间轴（0.5–2s），精确模式把边界修到 40ms 级；
- 用户需求固定时，策略随需求变，而不是固定跑全套。

## 3. 默认：详细转录

没有具体请求时：

```text
basic:
  Omni full profile
  → transcript + events + music
  → audio-score.json + hearing.md + context.md
  → 文本 LM 可用 context.md 问多个问题

precise:
  Omni full + Qwen ASR（词级）+ BEATs（事件）+ Beat This!（音乐）
```

## 4. 质量与取舍

- **targeted profile 可能漏掉未请求的事件**；只在用户明确要“只要笑声/只要掌声”时用。
- **默认 full**，保证“什么都听到”；用户明确缩小范围时才 targeted。
- **basic 的粗时间**能粗剪；**precise** 才做精剪/打轴。
- **quality first**：不为了省钱把用户要的事件漏掉；先用 Omni 召回，再用本地模型修时间。

## 5. 代码入口

```bash
# 默认详细转录
agent-ear listen long.mp4 --mode basic

# 只找笑声（粗时间）
agent-ear listen long.mp4 --mode basic --request "把视频里所有笑声都剪出来"

# 只找笑声 + 精确时间（不跑 ASR）
agent-ear listen long.mp4 --mode precise --request "把视频里所有笑声都剪出来"

# 显式指定
agent-ear listen long.mp4 --mode precise --need events --request "找掌声"
```

实现：

- `ear/requests.py`：自然语言 → intent/labels/needs
- `ear/omni.py`：`profile="full" | "events"`；长音频 120s 分块 + 2s overlap + 去重
- `ear/routing.py`：按 needs 决定 ASR/AED/beat
- `ear/cli.py`：`--request` 接入
