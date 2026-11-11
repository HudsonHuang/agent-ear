# Ear 第一轮水位评估（2026-11-11）

> 目的：在同一批音频上，比较 **无音频文本 LM**、**Ear 管线 + 文本 LM**、**Qwen3.8-Omni-Flash 单模型** 三条线。
>
> 结论先行：**在“听懂并回答”这件事上，Omni 单模型明显更强、更快、更便宜；Ear 管线的 QA 增益只有 +2.2pp，统计上不显著。Ear 的价值要转向“精确时间轴/节拍/可编辑证据”，而不是通用音频问答。**

## 1. 设置

| 项 | 值 |
|---|---|
| 数据 | MMAU-Pro short/single/close **100**（30 sound / 30 music / 30 speech / 10 mixed）+ CMDAR-main **80**（中文，9 类推理均衡） |
| 音频时长 | 合计 **1.054 小时**（MMAU 中位 ~15s；CMDAR 中位 ~27s） |
| 文本 LM | `qwen-plus`，temperature 0，MCQ 四选一，严格首字母 |
| Ear | Qwen Audio 3.1 filetrans + PretrainedSED BEATs Strong（40ms）+ Beat This!；`hearing.md` L1 |
| Omni | `qwen3.8-omni-flash`，单次音频+题目+选项；主结果 `thinking_budget=256` |
| Basic note | `agent-ear listen --mode basic` 生成 hearing note，再让 qwen-plus 回答；用来检查“压缩成 note”损失多少 |
| 评分 | exact match；`format_error` 单独统计；不做 Gemini judge |

## 2. 主结果

| 线 | 180 条总体 | MMAU-Pro 100 | CMDAR 80 |
|---|---:|---:|---:|
| 无音频（只有题+选项） | 56.7% | 42.0% | 75.0% |
| **Ear 管线 + qwen-plus** | **58.9%** | **43.0%** | **78.8%** |
| Qwen3.8-Omni-Flash（thinking 0） | 81.7% | 69.0% | 97.5% |
| **Qwen3.8-Omni-Flash（thinking 256）** | **87.2%** | **78.0%** | **98.8%** |

配对差：

- Ear − 无音频：**+2.2pp**（n=180；95% CI 约 ±7pp，**不显著**）
- Omni（thinking 0） − 无音频：**+25.0pp**
- Omni（thinking 256） − 无音频：**+30.5pp**
- Omni（thinking 256） − Ear：**+28.3pp**

分 domain（MMAU-Pro）：

| domain | 无音频 | Ear | Omni |
|---|---:|---:|---:|
| sound | 23.3% | 30.0% | **50.0%** |
| music | 53.3% | 50.0% | **83.3%** |
| speech | 50.0% | 56.7% | **73.3%** |
| mixed | 40.0% | 20.0% | **70.0%** |

**解读**：

1. Ear 只在 sound / speech 有小幅增益；music 下降 3.3pp，mixed 下降 20pp。说明当前的 `hearing.md`（BPM + 事件标签 + 分桶转写）不足以支撑音乐/混合推理，反而会干扰文本 LM。
2. Omni（thinking 256）在 CMDAR 上 98.8%，在 MMAU 上 78.0%，已经超过 Gemini 3.5 Flash 的公开 MMAU-Pro 分数（68.5%），接近 Gemini 3.1 Pro 的 72.2%。
3. 无音频 baseline 本身很高（CMDAR 75%），因为四选一选项有语言先验；**Ear 的 +2.2pp 不能当作有效水位提升**。

## 3. 成本与 RTF

| 线 | 平均每条 | 成本 | 备注 |
|---|---:|---:|---|
| Ear 管线 | **10.1s**（p50 11.2s / p90 14.1s） | Qwen ASR 约 **¥0.07/音频小时** + 本地计算 | 5 分钟音频 22.5s（约 13× 实时） |
| Omni answer（thinking 0） | **2.5s**（p90 4.6s） | **¥0.034/音频小时**（180 条合计 ¥0.036） | 平均 243 input / 2 output tokens；audio 147 tokens/条 |
| **Omni answer（thinking 256）** | **5.7s** | **¥0.141/音频小时**（180 条合计 ¥0.149） | **87.2%**；MMAU 78.0%，CMDAR 98.8% |
| Omni answer（thinking 512） | 5.5s（40 条子集） | ¥0.18/音频小时 | 子集 87.5%，与 256 持平；**256 足够** |
| Omni analyze（结构化，短音频） | 26.4s / 60s 音频 | 约 **¥0.35/音频小时** | 26 段转写 + 9 个笑声事件；timestamps 0.5s 级 |
| **basic 结构化，1 小时** | **231s（3.85min，RTF 0.064）** | **¥0.211/音频小时** | 30×2min 分块并行；1814 段语音 / 449 事件；schema OK |
| **precise 全量，5 分钟** | **57s（RTF 0.19）** | Omni + Qwen ASR + 本地 AED/beat | 190 段语音 / 44 事件；9 说话人（Qwen diarization 过切） |

结论：**Omni answer（thinking 256）比 Ear 更快、更便宜，而且准得多。** 这和“多 API 聚合一定更划算”的直觉相反；原因是 Omni 一次调用完成了 ASR + 事件 + 音乐语义，而 Ear 需要多次调用/多次本地推理，短音频的固定开销被放大。

> 注：Ear 的 10.1s 包含 ASR 上传/轮询、BEATs、Beat This!、融合；长音频摊薄后 5 分钟约 22.5s。Omni 的 2.5s 是短音频；**1 小时 basic 实测 231s（RTF 0.064，¥0.211/h）**，比按短音频外推更快，因为 2 分钟分块可并行。1 小时文件是 5 分钟样本循环 12 次，只用于 RTF/成本，不代表语义多样性。

## 4. Omni 的 ASR / 时间戳 / 事件

用 60 秒日语样本做结构化（`thinking_budget=256`）对比：

| 项 | Qwen ASR + Ear | Omni analyze |
|---|---|---|
| 转写段数 | 38（词级时间） | 26（0.5s 级） |
| 文本 CER（以 Qwen ASR 为参照） | — | **15.9%**（260 vs 258 字，编辑距离 41） |
| 说话人 | S0/S1，匿名 | S1/S2，匿名；轮次合理 |
| 事件 | BEATs 40ms，14 段笑声 | 9 段笑声，1–2s 粒度 |
| 音乐 | BPM 87 + beats/downbeats | “upbeat electronic background music”，**无 BPM/beat grid** |
| 耗时/成本 | 约 2.5s（60s，本地+ASR） | 26.4s，¥0.0058/60s |

**判断**：

- Omni 的 ASR 文本“够用”，但有 15.9% CER、段数更少、时间戳 0.5s 级；对白字幕、精确打轴、卡点不够。
- Omni 的事件是“语义级”的（能说“笑声/对话/音乐”），但不是 40ms 级；事件区间 1–2s，不能做精确剪辑。
- Omni 的音乐描述比 Ear 的 BPM 更有语义，但没有 beat grid，不能直接卡点。
- Omni 的 `thinking_budget=0` 只适合“回答 MCQ”；要结构化转写必须开 thinking，成本/延迟明显上升。

## 5. 失败分析

1. **Ear 的 note 太短/太粗**：MMAU 平均 note 954 字符；音乐题只有 BPM + 标签，sound 题只有通用 AudioSet 标签，mixed 题转写与事件互相干扰。
2. **文本 LM 不会“主动听”**：qwen-plus 只能读一次 note，不能回查 `audio-score`；而 Omni 可以反复看整段音频。这是架构差异，不是 PE 能完全补的。
3. **Ear 的 QA 增益集中在 speech**，但 speech 的 baseline 已经 50%；说明“转写”不是差异化能力。
4. **Omni 的强项是语义与联合推理**，弱项是精确时间/节拍；Ear 的强项正好相反。
5. **CMDAR 接近饱和**：97.5% 说明这个 80 条子集对 Omni 太简单；下一轮要加更难的中文/多语种子集，否则中文水位会虚高。
6. **precise 的 5 分钟样本被 Qwen diarization 切成 9 个说话人**（真实约 2 人）；长音频要显式 `--speakers 2` 或做说话人合并。
7. **事件 refine 只覆盖可映射标签**：34 个被 refine 的全是 Laughter；`bird chirping` / `spray hiss` 这类 Omni 开放标签仍是 `omni-coarse`。映射表/开放词表 SED 是下一步瓶颈。

## 6. 对架构的建议

### 6.1 默认模式（basic / QA）

**QA 走 `agent-ear ask`（Omni 直接听），不要走 `agent-ear listen` 的 note 再让文本 LM 读。** 40 条子集上：

| basic 的不同形态 | 准确率 |
|---|---:|
| `agent-ear ask` 一次调用：详细转录 + 回答（40 条子集） | 90.0%（子集，未复现） |
| 同上，180 条全量 | **80.0%**（MMAU 69.0 / CMDAR 93.8；2 条 JSON 解析失败） |
| `agent-ear ask` 只回答（40 条子集 / 180 条全量） | 87.5% / **87.2%** |
| `agent-ear listen --mode basic` + 富上下文 + qwen3.8-max | **77.5%** |
| `agent-ear listen --mode basic` + 富上下文 + qwen-plus | **65.0%** |
| `agent-ear listen --mode basic` 的压缩 note + qwen-plus | **55.0%** |

原因：压缩 note 只有 ~400 字符，损失太大；把 Omni 的完整转录/事件（`context.md`，~850 字符起）交给文本 LM，qwen-plus 从 55% 升到 65%，qwen3.8-max 到 77.5%。**所以 basic 的主形态是“详细转录 + 富上下文”，不是压缩 note。**

- `agent-ear listen --mode basic`：一次 Omni → 完整 transcript/events/music → `audio-score.json` + `hearing.md` + `context.md`。它是**详细转录/描述模式**，时间戳 0.5–2s，能支持粗剪，但打轴不够。
- `agent-ear ask --score <dir> "问题"`：拿保存的 `context.md` 问文本 LM，**不再调 Omni**；可以问多个问题。
- `agent-ear ask <audio> "问题"`：一次 Omni 同时返回完整分析 + 答案；适合“既要转录又要答案”的一次性场景。**注意**：40 条子集 90.0%，但 180 条全量只有 80.0%，比只回答低 7.2pp；dual-task/JSON 长度会伤答案。单问题最高准确率仍用只回答模式。

差多少、为什么，见 [直接 ask vs 转录后 ask](direct-vs-transcribe.md)。

- 更准（87.2% vs 58.9%，thinking 256）
- 仍更快（5.7s vs 10.1s/短条）
- 仍然便宜（¥0.141/h vs Qwen ASR + 本地计算；quick 模式 ¥0.034/h）
- 架构简单：一次 API，直接 audio + question。

Skill 仍可保留：负责选择 Omni、构造 prompt、解析答案、缓存、成本控制；但不再需要 PANNs/BEATs/Beat This! 参与 QA 链路。

### 6.2 精确/剪辑模式（edit）

保留 Ear 管线：

- Qwen ASR 词级时间 + BEATs 40ms 事件 + Beat This! beats/downbeats；
- 输出 `audio-score` / `timeline` / `cut_candidate`；
- Omni 的 0.5s 时间戳和 1–2s 事件不够精确，不能替代。

### 6.3 混合模式（可选）

- **Omni 做语义层**（场景、情绪、音乐描述、事件语义）；
- **Ear 做时间层**（词级/40ms/beat grid）；
- 两者合并成 `audio-score`，用 Omni 的叙事补 Ear 的语义空白，用 Ear 的时间补 Omni 的精度。
- 成本/延迟会增加；只在“deep / 影视级”需要时启用。

## 7. 下一步

1. **默认 QA 走 `agent-ear ask`（Omni thinking 256）**；`agent-ear listen --mode basic` 只做结构化时间轴。1 小时 basic 已测：231s、¥0.211/h；下一步补 1 小时 `precise`。
2. **Ear 管线保留为 `--mode edit`**，只服务精确时间/卡点/本地隐私；不再宣称“通用音频 QA 更强”。
3. **中文评估加难**：CMDAR 97.5% 已饱和；补 open-ended / 更长 / 更多方言的 30–50 条，避免虚高。
4. **Omni analyze 的时间戳**：用 20 条人工标注音频测 onset/offset 误差；如果 0.5s 级稳定，可作为“非剪辑”字幕/摘要；否则只做语义层。

## 8. 数据与可复现

- 结果文件：`eval/results/no_audio.jsonl`、`ear_hearing.jsonl`、`ear_qa2.jsonl`、`omni_full_off.jsonl`、`omni_256.jsonl`、`omni_analyze_sample.jsonl`。
- 脚本：`eval/run_eval.py`、`eval/run_omni.py`、`eval/report.py`、`eval/note.py`。
- 数据：`eval/data/`（gitignore，不提交音频）。
- 许可：MMAU-Pro CC-BY-NC 4.0；CMDAR MIT（电影片段版权归原方）。仅内部评估。
