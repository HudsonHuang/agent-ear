# Ear Skill：前期分析与设计 v0.1

> **目标**：让没有音频感受器的语言模型，通过一个 Skill 获得接近正常人的「统一听觉」——不是分别做 ASR、AED、BPM，而是把语音、音乐、声音事件放在同一条时间线上联合理解，输出任何 LM 都能读的本地记录。
>
> **约束**：重模型走云端（Qwen Audio 3）；本地只跑小模型（节奏、事件）；不同机器上的 RTF 要稳定；主要面向视频剪辑、音频剪辑、转录。
>
> **日期**：2026-11-11

---

## 0. 结论先行

1. **方向成立，而且生态里确实缺这个东西。** 现有音频 MCP/Skill 几乎都是「Whisper 包装」：转写、字幕、摘要。真正把语音、事件、音乐融合成一条可查询时间轴的实现，公开项目里几乎为零；最接近的 `audio-intelligence-mcp` 只有 1★。这不是红海里的又一个 wrapper。
2. **单模型替代不了。** Omni 模型（Gemini、Qwen-Omni、GPT-audio 这一类）能「描述」音频，但给不了 beat grid、精确 onset、可靠 diarization；而剪辑场景要的恰恰是这些「数字」。Omni 适合做语义旁白和路由，不适合做测量仪。
3. **你的三层划分是对的，但真正的难点在融合层。** 三份结果拼在一起，LM 读到的仍然是三份报告；只有统一时钟、类型化实体、关系图、显著性排序、多分辨率视图都到位，才叫「联合分析」。
4. **语音层用云端 Qwen Audio 3.1 filetrans 是正确选择。** 它一次返回词级时间戳、`speaker_id`、标点、置信度；项目内实测 991s 音频纯推理 31.4s（约 31× 实时），16.5 分钟高光总墙钟 41.7s。**不需要本地方案，也不需要再跑 forced aligner。**
5. **「Google AudioFM」需要替换或确认。** 公开可查的 AudioFM 是 2026-10 的论文（arXiv 2610.34183），页面上没有代码/权重/API 链接；它不是能直接 `pip install` 的小模型。可落地的本地 AED 默认应是 **PretrainedSED BEATs Strong**（BEATs + AudioSet Strong 头，447 类，40ms，364MB，MIT）；PANNs 只作 fallback，语义描述再让 omni 模型补。
6. **节奏检测：librosa 不够，用 Beat This!。** `small0` 只有 8.1MB，MIT，输出 beats + downbeats；在公开对比中 beat F 0.872 / downbeat F 0.846，而规则型 DSP 是 0.506 / 0.080。**downbeat 是「卡点」的关键，librosa 根本不输出 downbeat。**
7. **1 小时音频的基础链路预算约 4–6 分钟**（Qwen 约 2 分钟 + Beat This! 约 1–3 分钟 + BEATs 约 10 秒级 + 融合秒级）。这个量级对离线剪辑是可接受的；重模式（Demucs、All-In-One）要异步跑。
8. **最小成本不是「少调 API」，而是「一套稳定契约」。** 一条 CLI、一个 `audio-score` schema、一份 digest、一个 query 接口；任何 LM 都能接。API 编排只是实现细节，融合层和输出格式才是这个 Skill 的护城河。

**一句话**：这个 Skill 不是「音频版 OCR」，而是「把音频编译成 LM 可推理的证据图谱」；Qwen 负责听清人话，BEATs Strong/Beat This! 负责听出声音和节拍，融合层负责把它们变成「一个人会怎么描述这段声音」。

---

## 1. 判断标准：什么叫「正常人的统一听觉」

WER、mAP、beat F1 都是零件指标。这个 Skill 的目标是「联合听觉」，应该按下面 6 个维度验收：

| 维度 | 正常人能做到 | Skill 应该输出 |
|---|---|---|
| 场景与前景 | 知道这是采访/演唱会/游戏，知道什么是背景 | 场景标签、前景/背景、speech/music/event 占比 |
| 语音 | 听清内容、谁在说、语气、笑/叹气/咳嗽 | 词级转写、说话人轮次、非语音发声、韵律/情绪 |
| 音乐 | 知道有没有歌、什么情绪、大概什么段落在重复 | BPM、beats/downbeats、段落标签、genre/mood/instruments |
| 事件 | 听到掌声、玻璃碎、门响、键盘声，并能定位 | AudioSet 事件 + 起止时间 + 置信度 + 显著性 |
| 联合 | 「笑声在包袱之后」「人声压在音乐上」「这一刀没卡在重拍」 | 关系边：after / over / at / causes / contrast |
| 校准 | 不确定就说「像是掌声，但不敢确定」 | confidence、uncertain、warnings，禁止把猜测写成事实 |

验收不该是「转写对了多少字」，而应该是：给 30 段真实素材、每段 20 个问题，让 Skill + 一个文本 LM 回答，和人类听一遍的答案对比。问题覆盖「发生了什么 / 谁在说 / 什么时候 / 和音乐什么关系 / 该从哪里下刀」。评分看联合推理和定位，不只看 WER。

---

## 2. 现有方案盘点：为什么还值得做

### 2.1 原生能听音频的模型/客户端

| 入口 | 能否直接听 | 输出形态 | 对剪辑够不够 |
|---|---|---|---|
| Claude Code | **不能**（Read 不支持音频） | — | 结构性失聪；这正是最高价值的用户群 |
| Codex | 有条件：模型支持音频时可传，约 50MiB 上限 | 散文/转写 | 能描述，不能给 beat grid |
| Gemini CLI | 能，约 20MB 上限 | 散文，可要求 MM:SS | 时间戳会漂，不能做精确剪辑 |
| ChatGPT 桌面/网页 | 能，音频上传上限很大 | 散文/转写 | 同上，且不可编程 |
| 直接调 API | Gemini / OpenAI 支持音频；Anthropic Messages 没有 audio block | 散文/JSON（靠 prompt） | 没有稳定 schema |

结论：**宿主不一定有耳朵；即使有，也是「描述」而不是「可编辑的时间轴」。** 这个 Skill 的价值是跨宿主、可编程、可缓存、可 diff。

### 2.2 现有 Skill / MCP

| 项目 | 能力 | 差距 |
|---|---|---|
| `watch-skill`（568★） | 视频/音频/屏幕 → 带时间戳的证据库 | 音频只做转写，没有 AED/音乐 |
| `audio-intelligence-mcp`（1★） | Whisper + PANNs + VAD + 可选 pyannote，输出 JSON envelope | 最接近，但单作者、未验证、无融合语义 |
| `mcp-server-whisper`（60★） | Whisper 转写 | 纯语音 |
| `transcriptor-mcp`（24★） | 转写 + 章节 | 纯语音 |
| `mcp-music-analysis`（34★，已停更） | librosa + whisper | 音乐分析很浅 |
| Anthropic 官方 skills | 文档/表格/PPT/PDF，共 19 个 | **没有任何音频/视频 skill** |

结论：**生态是 speech-shaped 的**。再做「又一个 Whisper MCP」没有意义；缺的是「融合后的 ear map」——统一时钟、事件关系、置信度、可查询。

### 2.3 统一 omni 模型够不够

Omni 模型确实在进步，但它们的能力结构不适合这个任务：

- **能叙述，不能测量。** 你问「这段音乐什么感觉」它能答；你问「第 37 小节的 downbeat 在哪」它给不了。
- **时间戳会漂。** 长音频上，模型靠 token 位置推断时间，误差会累积；不同入口（user turn vs tool response）精度还不一样。
- **细粒度声音识别弱。** 大类（音乐/语音/噪声）还行，细类（玻璃碎/硬币掉落/特定警报）显著下降，而且会很自信地答错。
- **音乐推理接近随机。** 和弦、节拍、结构这些，omni 不如专用模型；公开的 omni 音乐基准里，很多模型只比「不听」好一点。

所以正确的分工不是「omni 替代 pipeline」，而是：

> **Omni 负责「这段声音像什么、值不值得深挖」；专用模型负责「准确的时间、节拍、说话人、事件类别」。**

### 2.4 你机器上已经有的能力，不要重复造

这台机器上已经装了 `arkcli-understand`（`vau` 音视频联合理解、`asr`、`asr-align`、`asr-speakers`）和 `bailian-gen`（`bl speech recognize`、`bl omni`）。它们已经能：

- 把音频转成文本/字幕；
- 做多说话人转写（`asr-speakers`）；
- 对视频做音视频联合理解（`vau`），输出一段「声音分析报告」。

所以 Ear **不要**再做一个「调用 ASR 的 Skill」——那会和现有能力重叠。Ear 的差异化只有三点：

1. **统一时间轴**：把 Qwen 的词级时间、BEATs Strong 的事件、Beat This! 的节拍放在同一个时钟上；
2. **融合关系**：谁压在谁上、笑声在哪个包袱后、切点离 downbeat 多远；
3. **剪辑动词**：`find` / `context` / `beats --format edl` / `export srt`，让 LM 能直接下刀。

现有 `vau` 可以作为「语义旁白」后端之一，但不作为时间/节拍的来源。

---

## 3. 三层模型的修正：从「三路并行」到「证据层 + 融合层」

你说的三层——事件、音乐、人声——作为内容分类是对的。但工程上要补三件事，否则 LM 仍然是在读三份互不相干的报告。

### 3.1 补第 0 层：Probe（先花 10 秒判断值不值得听）

不是所有音频都需要跑全套。先做：

- `ffprobe`：时长、采样率、声道、码率、容器；
- 响度（EBU R128）、峰值、静音比例、削波；
- Silero VAD：语音占比、语音段分布；
- 音乐/语音分类（一个小 CNN 或 PANNs 的 music/speech 标签）；
- 语言 ID（可用 Qwen 的首段结果，或轻量 LID）。

输出一个 `probe.json`，决定后面跑哪些层、用什么预算。**这一步能把「1 小时播客」和「30 秒特效素材」路由到完全不同的链路。**

### 3.2 补第 4 层：Fusion（把三段变成一段）

融合层要做的不是拼接，而是：

1. **统一时钟**：所有层用同一个 `[start_ms, end_ms)`，以源文件为唯一原点；视频要记录帧率与 `pts` 偏移。
2. **类型化实体**：`speech` / `music` / `event` / `silence` / `non_speech_vocal`，每个都有稳定 ID。
3. **关系边**：`after`、`over`、`at`、`during`、`contrast`、`repeat_of`。例如「笑声 ev_12 在 sp_08 结束后 320ms」「sp_08 压在 mu_03 上」「cut_candidate 在 downbeat 上」。
4. **显著性**：前景/背景、能量、是否被掩蔽。人耳会自动做这件事，模型不会。
5. **结构**：章节、音乐段落、说话人轮次、静音间隙——这是「一分钟看完 1 小时」的骨架。
6. **校准**：每个结论带 `source`、`confidence`、`uncertain`；融合层不能凭空生成事件。

**没有融合层，三层只是三份 transcript；有了融合层，才是「一段声音的证词」。**

### 3.3 长音频：先索引，再精听（比「全量精听」更好的形态）

正常人不会把 3 小时直播从头到尾逐字听一遍；他们会**拖进度条、看波形、跳到有反应的地方**。Skill 也应该这样：

1. **粗索引（全片，便宜）**：VAD 语音段、能量峰值、PANNs 事件峰、音乐/语音比例、CLAP/音频嵌入（可选）。输出一个 `index.jsonl`，每 5–10 秒一行。
2. **查询/检索**：`ear find --event Laughter`、`ear find --query "像掌声"`（嵌入）、`ear find --silence`。只召回候选窗口。
3. **精听（按需，贵）**：只对候选窗口跑 Qwen 词级转写、Beat This!、PANNs 细分类。结果回填到 score。
4. **迭代**：LM 可以 `agent-ear listen --window 00:12:00-00:12:30` 反复听一个点，像人一样「倒回去再听一遍」。

这样 1 小时视频的默认成本是「索引 + 少量精听」，而不是「全量转写 + 全量节拍」。**这也是 Agent 化听觉的关键：不是一次性生成一份大报告，而是提供一个可以反复询问的耳朵。**

### 3.4 补「显著性」和「关系」，因为人耳听的是关系

正常人听一段视频，记住的不是「有音乐、有语音、有笑声」，而是：

- 笑声出现在哪句话之后，为什么好笑；
- 音乐在哪个点突然变大，和画面切换是否同时；
- 说话人什么时候被打断，语气有没有变；
- 这一刀是不是卡在重拍上。

这些全是**关系**。所以 `audio-score` 的核心不是三个数组，而是 `relations[]`。这也是后面所有剪辑动词的基础。

---

## 4. 各层选型

先把「原始设想 → 建议」的取舍摆出来，后面每节再展开：

| 原始设想 | 建议 | 理由 |
|---|---|---|
| AED 选 Google AudioFM | 默认 PretrainedSED BEATs Strong；PANNs 仅 fallback；语义旁白用 omni | AudioFM 无权重/API；BEATs Strong 是 40ms / 447 类的 AudioSet Strong 帧级模型 |
| 音乐用「节奏检测」 | Beat This! small0（8.1MB，beats+downbeats）；All-In-One 仅做段落 | librosa 没有 downbeat，卡点不够 |
| 人声用本地 ASR/MOSS/Qwen | **云端 Qwen Audio 3.1 filetrans** | 跨机器 RTF 稳定；词级时间 + speaker_id 一次给全 |
| 三份结果 + 本地 gzip JSON | 一个 `audio-score` + 融合层 + 多分辨率 digest | 三份 JSON 不是联合分析；LM 读不下全量 |
| 默认模式=人声+事件+节奏 | Probe 路由 + **default / music / privacy** 三模式 | 1 小时播客和 30 秒特效不该走同一链路 |

### 4.1 语音层：Qwen Audio 3.1 filetrans（云端）

**用你项目里已经验证过的 `qwen-audio-3.1-asr-flash-filetrans`**，不要本地 Qwen3-ASR，不要 MOSS/Whisper。理由：

- **RTF 跨机器稳定**：云端 31× 实时，不受用户电脑影响；本地大模型在 16GB Mac 上会退化到 1× 实时甚至更慢。
- **一次调用给全**：`text`、`sentences[]`、`speaker_id`、`words[]`（`begin_time`/`end_time`/`text`/`punctuation`/`confidence`）。
- **不需要 forced aligner**：词级时间戳已经在返回里；你项目里 Qwen3-ForcedAligner 那套可以完全不用。
- **成本可忽略**：项目实测约 ¥0.07/音频小时；1 小时约 2 分钟。

**关键限制（必须写进 Skill 的 warnings）**：

- **短窗口 diarization 会塌**：项目黄金集里，44–113s 的短高光，Qwen 的 cue 级说话人准确率 66.7%，低于本地 MOSS+声纹的 82.5%；有些窗口会塌成单说话人。长窗口（>5–8 分钟）Qwen 反而明显更好。
  - 对策：文件 < 90s 时，`speaker_count` 钉死 2，或加 ±120s 上下文，或只输出「匿名轮次」并标 `speaker_confidence=low`；不要让下游把 S0/S1 当身份。
- **唱歌段文本会崩**：项目实测歌曲段 MOSS 与 ASR2 文本差异大，字级对齐覆盖只有 43–59%。对策：音乐占比高的文件，先 Demucs 分离人声，再送 Qwen；歌词段单独标 `lyrics`，不和对话混在一起。
- **热词/语言提示**：`language_hints`、`vocabulary` 要暴露给 Skill 参数；对日语/中文/专有名词很关键。
- **上传**：复用你项目里的 TOS 签名 URL / DashScope `oss://` 兜底；这是已经踩过坑的路径。

**输出映射**：`sentences[].speaker_id` → `speaker`（匿名 `S0`/`S1`），`words[]` → `words`；`confidence` 保留；`content_duration` 用于 speech ratio。

### 4.2 事件层：AudioFM 的现实与替代

这里要先把一个事实说清楚：**公开可查的 Google AudioFM 是论文，不是可调用的小模型。**

- arXiv 2610.34183（2026-10-25）：*AudioFM: Towards General Purpose Audio Representation Learning*，自监督音频表示，线性探测/微调/零样本 SOTA；页面上没有代码、权重、API 链接。
- 如果你说的是 **NVIDIA Audio Flamingo 3**：它是数 B 级的音频 LLM，CC-BY-NC、约 10 分钟输入上限，输出散文，不给时间戳；不是「小模型」，也不适合作为可分发的 Skill 依赖。
- 如果你说的是某个内部/第三方 `audiofm` 服务：请告诉我 endpoint/模型名，我按那个接；否则默认走下面的替代。

**可落地的本地 AED 默认栈**：

| 方案 | 体积 | 许可 | 输出 | 评价 |
|---|---|---|---|---|
| **PretrainedSED BEATs Strong** | 364MB | MIT | 447 类 AudioSet Strong，40ms 帧级，onset/offset | **默认**；PSDS1 46.5；60s 约 2.5s（含加载） |
| PretrainedSED ATST-F Strong | 344MB | MIT | 447 类，40ms 帧级 | 备选；PSDS1 45.8 |
| PANNs CNN14 | 327MB | MIT | 527 类，clip-level / 5s 窗口 | **fallback**；旧特征、时序弱 |
| YAMNet | 约 4MB | Apache-2.0 | 521 类，0.96s patch | 极轻兜底 |
| CLAP | 约 150M | CC0 代码 | 零样本标签，clip 级 | 适合检索，不给时间戳 |
| Qwen-Omni / Gemini | 云端 | — | 散文描述 | **只做语义旁白，不做时间** |

> MVP 默认用 **PretrainedSED BEATs Strong**：AudioSet Strong 帧级 447 类，40ms；解码阈值 0.30 + 200ms median filter，输出 onset/offset。PANNs 只在 BEATs checkpoint 缺失时 fallback。

**工程要点**：

- PANNs 输出是帧级 sigmoid，不能直接当事件；要做 per-class 阈值 + 中值滤波 + 合并 + 最短时长，才能得到 `[start,end,label,conf]`。
- 事件标签要映射到「人话」：AudioSet 的 `Laughter`、`Applause`、`Glass`、`Whoosh` 保留英文键，同时给中文显示名。
- 重叠事件会合并/漏检；对低能量事件要允许 `uncertain`，不要硬报。
- 语义旁白（「这段像咖啡馆」「这是紧张的打斗配乐」）用 omni 只对**选中的 10–30 秒窗口**跑，不要整段跑；这样既便宜又准。

### 4.3 音乐层：节奏检测到底用不用模型

这是你点名要调研的部分。结论：**librosa 不够；用 Beat This!，而且优先 `small0`。**

| 方案 | 体积/依赖 | 输出 | 速度 | 结论 |
|---|---|---|---|---|
| **librosa** `beat_track` | 纯 Python，无模型 | BPM、beat 帧 | 很快 | 只适合做 probe/兜底；**没有 downbeat、没有段落**；对速度变化、弱起音、自由节奏会崩 |
| **Beat This!** `small0` | **8.1MB** 权重；PyTorch | beats + downbeats | Mac CPU 约 3s/60s（full 模型），small 更快 | **默认**；MIT；卡点够用 |
| Beat This! `final0` | 78MB | beats + downbeats | 同上 | 质量优先时用；和 small0 同一接口 |
| **All-In-One** | 轻量模型，但依赖 Demucs + madmom + NATTEN（约 2GB 栈） | BPM、beats、downbeats、段落 + 标签（intro/verse/chorus/bridge/outro） | 33 分钟音频在 4090 上 73s；Mac CPU 慢很多 | **可选**；只有需要「段落/chorus」时才跑 |
| BeatNet | PyTorch，CC-BY-4.0 | beats/downbeats/meter，实时 | 中等 | 实时场景更合适；离线不必 |
| Essentia | C++/Python，AGPL/商业双许可 | BPM/key/结构 | 快 | 许可不适合分发性 Skill |

**为什么说「显著优于 librosa」**：

- 在一份 2026-10 的实测里（60 首 DJ 曲库，djay Pro 网格作参考），规则型 DSP 的 beat F 是 0.506、downbeat F 只有 **0.080**；Beat This! 是 **0.872 / 0.846**。差距不是几个点，是一个数量级。
- librosa 的 `beat_track` 是「onset strength + 动态规划」，本质是规则型 DSP；它不输出 downbeat，也不理解段落。对剪辑来说，「第一拍/重拍」比「平均 BPM」重要得多。
- Beat This! 是 ISMIR 2024 的 transformer，20.3M 参数；`small0` 是 8.1MB 的小模型版（`--transformer-dim=128`）。它不依赖 DBN 后处理，输出就是 beat/downbeat 两个分数序列，峰值拾取即可。

**建议的默认策略**：

1. Probe 判定 `music_ratio > 0.15` 才跑节奏；纯语音/环境音不要跑，否则是噪声。
2. 默认 `Beat This! small0`；如果素材是复杂编曲/现场演奏，切 `final0`。
3. 输出 `bpm`、`beats[]`、`downbeats[]`、`beat_positions[]`（1–4）、`confidence`。
4. 需要段落时再加 `All-In-One`，输出 `sections[]`（intro/verse/chorus/bridge/outro）；不要为了段落把 All-In-One 变成默认依赖。
5. librosa 只保留为「零依赖兜底」：没有 torch/模型时给 BPM 和粗略 beat，并明确标 `quality=fallback`。

**跨机器 RTF 的工程建议**：

- 不要把 PyTorch 作为分发依赖。Beat This! 已有 ONNX / CoreML 导出实践（int8 约 20–23MB，精度几乎不掉）；PANNs 也可以导出 ONNX。
- Skill 的本地运行时优先 **ONNX Runtime**（CPU），把「模型」变成几十 MB 的文件，而不是 2GB 的 torch 栈。这样 Windows/Mac/Linux 的 RTF 才稳定。
- MVP 阶段可以先用 PyTorch 跑通；但发布形态应该是「ffmpeg + onnxruntime + 两个小模型 + Python 薄层」。

### 4.4 音乐语义（可选，属于 music 模式）

- **genre/mood/instruments**：Qwen-Omni / Gemini 对 10–30 秒窗口做旁白，准确度够用；不要让它们给时间。
- **歌词**：Demucs 分离人声 → Qwen filetrans；带词级时间戳；如果已有官方歌词，走「官方歌词 + 对齐」而不是 ASR 当真值（你项目里的经验）。
- **转谱**：basic-pitch 可以给单音/钢琴的 note events；复调总谱不在 default 模式承诺范围内。这是 music 模式的能力，不要写进默认承诺。
- **多轨转谱 API**：真正自助的 full-mix → per-instrument MIDI 目前只有 **Mirelo Audio-to-MIDI Pro**（需先 eval）；**Klangio 是单乐器**（piano/guitar/bass/drums/vocal 等）；Music.ai 是模块化（和弦/节拍/段落/歌词/stems），不提供 per-instrument MIDI；Songscription 多乐器但 API 仅 Enterprise。music 模式优先接这些，不要自研引擎。详见 [前置判断 §7](prior-art-and-necessity.md#7-音乐模式调研结论与建议)。

---

## 5. 统一记录格式：`audio-score`

### 5.1 设计原则

1. **一个时钟**：全部毫秒，`[start_ms, end_ms)`，源文件为原点；视频记录 `fps` 和 `pts_offset_ms`。
2. **稳定 ID**：`sp_0001`、`mu_0001`、`ev_0001`、`ch_01`；跨版本可 diff。
3. **证据链**：每个实体有 `source`（qwen/beat_this/panns/allin1/omni）、`confidence`、`uncertain`。
4. **能力声明**：`capabilities` 说明这次跑了什么、没跑什么；LM 不会把「没跑」当「没有」。
5. **多分辨率**：`one_line` → `chapters` → `timeline_10s` → `full`；默认只把前两级给 LM，细节按需查询。
6. **双表示**：`score.json` 给工具和查询；`hearing.md` 给 LM 读——一页「我听到了什么」，每句带时间戳。
7. **可缓存**：`sha256(file) + config` 作为 key；gzip 存储；重复分析零成本。

### 5.2 骨架

```json
{
  "schema": "ear.score/1",
  "source": {
    "path": "/abs/path/video.mp4",
    "sha256": "…",
    "duration_ms": 183000,
    "fps": 29.97,
    "pts_offset_ms": 0
  },
  "capabilities": {
    "speech": "qwen-audio-3.1-filetrans",
    "music": "beat_this-small0",
    "events": "panns-cnn14",
    "structure": null,
    "fusion": "rules-v1"
  },
  "global": {
    "summary": "两人室内对话，背景轻音乐；00:42 出现笑声，01:10 音乐切到鼓点更强的段落。",
    "speech_ratio": 0.71,
    "music_ratio": 0.22,
    "event_ratio": 0.07,
    "speakers": 2,
    "languages": ["ja"],
    "scene": "indoor / vlog",
    "mood_curve": [{"t_ms": 0, "label": "轻松"}, {"t_ms": 70000, "label": "兴奋"}]
  },
  "speech": {
    "segments": [
      {
        "id": "sp_0001",
        "start_ms": 160,
        "end_ms": 2760,
        "speaker": "S0",
        "lang": "ja",
        "text": "はい、ということで ここからは ですね。",
        "words": [{"t_ms": 160, "d_ms": 320, "w": "はい", "conf": 1.0}],
        "conf": 0.98
      }
    ],
    "turns": [{"speaker": "S0", "start_ms": 160, "end_ms": 16920}],
    "non_speech_vocal": [{"id": "ev_0012", "type": "Laughter", "start_ms": 42000, "end_ms": 44500}]
  },
  "music": {
    "tracks": [
      {
        "id": "mu_0001",
        "start_ms": 0,
        "end_ms": 70000,
        "bpm": 92,
        "beats_ms": [330, 982, 1634],
        "downbeats_ms": [330, 2938, 5546],
        "beat_positions": [1, 2, 3, 4],
        "sections": [{"start_ms": 0, "end_ms": 70000, "label": "intro"}],
        "genre": null,
        "mood": "轻松",
        "vocals": false
      }
    ],
    "lyrics": []
  },
  "events": [
    {"id": "ev_0012", "start_ms": 42000, "end_ms": 44500, "label": "Laughter", "label_zh": "笑声", "conf": 0.81, "salience": 0.9}
  ],
  "relations": [
    {"type": "after", "from": "ev_0012", "to": "sp_0008", "gap_ms": 320},
    {"type": "over", "from": "sp_0001", "to": "mu_0001"},
    {"type": "cut_candidate", "at_ms": 70120, "reason": "downbeat + section_change"}
  ],
  "views": {
    "one_line": "…",
    "chapters": [{"start_ms": 0, "end_ms": 60000, "title": "开场"}],
    "timeline_10s": ["0–10s：…", "10–20s：…"]
  },
  "warnings": ["file < 90s: speaker labels may collapse to one speaker"],
  "provenance": {
    "created_at": "2026-11-11T11:00:00+08:00",
    "tool_version": "0.1.0",
    "params": {"language_hints": ["ja"], "speaker_count": 2}
  }
}
```

> 真实文件里 `beats_ms`/`words` 会很大。**不要把这些数组塞进 LM 的 context**：完整数组留在 gzip JSON/JSONL 里，digest 只给摘要和引用。

### 5.3 多分辨率与 context 预算

| 层级 | 内容 | 1 小时约多少 token | 用途 |
|---|---|---|---|
| L0 `one_line` | 2–3 句整体描述 | 80–150 | 路由、标题、首屏 |
| L1 `chapters` | 8–15 个章节，每章 1 句 | 400–800 | 「先看骨架」 |
| L2 `timeline_10s` | 360 条 10 秒摘要 | 3k–6k | 找片段、定位 |
| L3 `full` | 词级转写 + 事件 + beats | 20k–60k | 精确剪辑/字幕；按需查询 |

**默认只给 L0+L1**；用户问「哪里」再 `ear context --query` 拉 L2/L3 的相关窗口。这是让 1 小时视频在 agent 里「可读」的关键。

### 5.4 查询接口（模型无关）

Skill 不绑定某个 LM，只提供证据包：

```bash
agent-ear listen video.mp4 --mode default --out .ear/<hash>
agent-ear digest .ear/<hash> --level 1
ear context .ear/<hash> --query "笑声" --window 30
ear find .ear/<hash> --event Laughter --min-conf 0.6
ear beats .ear/<hash> --format edl
ear export .ear/<hash> --format srt,hearing.md
```

`ear context` 返回的是「相关窗口的 score 切片 + 前后文 + 时间戳」，由宿主 LM 做推理。这样 Claude、GPT、DeepSeek、Gemini 都能用，不绑 joint-train 的模型。

---

## 6. 典型任务：现在因为「没耳朵」做不到，或做得很痛

### A. 视频/音频剪辑（核心场景）

| 任务 | 没耳朵的模型为什么做不到 | Ear 的输出 |
|---|---|---|
| **卡点混剪**：把 12 个镜头卡在鼓点/重拍上 | 只有 BPM 不够，需要 downbeat 和小节位置 | `beats/downbeats` + `cut_candidate` + 可执行 EDL |
| **长视频高光**：从 3 小时直播里找 8 个「观众笑了」的瞬间 | 转写只能看文字，笑声/掌声/惊呼不在文本里 | 事件时间轴 + 语音上下文 + 显著性排序 |
| **SDH 字幕**：`[笑声]` `[门关上]` `[音乐渐强]` | 转写没有非语音事件；字幕工具不会听 | 事件 + 时间 + 说话人 + 字幕行 |
| **播客/直播切片**：章节、广告口播、静音、口头禅 | 转写有文字但没节奏/音乐/停顿 | 章节 + 静音图 + 语速/停顿 + 音乐床 |
| **MV/歌词视频**：歌词、段落、卡点 | 需要 lyrics + beat + section 三者对齐 | 歌词行 + 词级时间 + chorus 段落 + downbeat |
| **预告片/混剪**：把重音落在画面切换上 | 需要音乐能量曲线和 hit point | 能量曲线 + downbeat + 切换建议 |
| **配音/译制 QA**：漏句、口型、时长 | 需要原声/配音的语音时间轴对比 | 双边词级时间 + 缺失/超长检测 |
| **游戏/体育集锦**：击杀、哨声、欢呼 | 事件不在转写里 | 事件 + 峰值 + 前后 3 秒 |
| **降噪/修复 QA**：电流声、削波、断音 | 需要信号层指标 | 噪底/削波/断音段 + 时间戳 |
| **音效/B-roll 检索**：找「whoosh」「玻璃碎」 | 文本检索不到声音 | 事件索引 + 相似片段 |

### B. 生成式模型的自修正（你提到的「自己听不了」）

| 任务 | 现状 | Ear 如何闭环 |
|---|---|---|
| **视频生成**（Sora/Veo/可灵/OPS 这类） | 能生成画面和音频，但听不了自己的输出；音效对不上、环境声断层、音乐情绪不对 | Ear 读输出 → 结构化批评（哪一秒、什么错、置信度）→ 生成器改 prompt/重生成 → Ear 复检 |
| **TTS/有声书** | 能合成，但漏字、读音错、停顿怪、情绪不对 | 词级对齐 + 漏字检测 + 语速/停顿曲线 → 自动重试 |
| **播客生成**（双人对谈） | 轮次重叠、抢话、笑声不自然 | 说话人轮次 + overlap + 非语音发声 → 调整脚本/重生成 |
| **音乐生成** | 结构乱、卡点不准、人声不清 | section + beat grid + 歌词清晰度 → 编辑/重生成 |
| **预告片自动生成** | 画面剪了，但音乐没落点 | 能量/downbeat 对齐 → 自动挪切点 |
| **配音本地化** | 翻译对了，但口型/时长不对 | 双边时间轴 + 超长/缺失 → 重配 |

**这是这个 Skill 最大的想象空间**：它不是「给模型加一个转写工具」，而是给生成模型一个**可执行的听觉奖励信号**。生成器不需要变成 audio-native，只要能被 Ear 批评，就能迭代。

### C. 知识与无障碍

| 任务 | 没耳朵的痛点 | Ear 的输出 |
|---|---|---|
| 会议/语音备忘录 | 只有转写，没有谁打断谁、语气、决议 | 说话人轮次 + 打断 + 语气 + 章节 + action item 候选 |
| 客服质检 | 合规词、情绪、静音、背景噪 | 情绪曲线 + 静音/噪音 + 关键词时间 |
| 课程/视频笔记 | 章节靠猜，公式/板书朗读丢失 | 章节 + 公式朗读段 + Q&A 段 |
| 屏幕录制调试 | 报错音/提示音和画面事件对不上 | 事件 + 与画面时间对齐（需视频帧） |
| 音频档案检索 | 只能按文件名/转写搜 | 「找笑声」「找副歌」「音乐什么时候停」 |
| 无障碍 | 盲人需要声音描述；聋人需要 SDH | 场景/事件叙述 + SDH 字幕 |
| 语言学习 | 只纠语法，不纠发音/流利度 | 词级时间 + 停顿 + 语速 + 重音（基础版） |
| 数据集清洗 | 人工听，慢 | 自动标签 + 重复/翻唱/静音检测 |

---

## 7. 可行性与性能预算

### 7.1 1 小时音频的端到端预算

| 阶段 | 方案 | 预计耗时 | 备注 |
|---|---|---|---|
| 上传 + Qwen filetrans | 云端 | 2–3 分钟 | 项目实测 31× 实时；上传取决于带宽 |
| Beat This! small0 | 本地 CPU/ONNX | 1–3 分钟 | full 模型 Mac CPU 约 3s/60s；small 更快 |
| BEATs Strong | 本地 CPU | <1 分钟 | 364MB，40ms 帧级；60s 约 2.5s |
| Probe/VAD/响度 | 本地 ffmpeg | 10–30 秒 | 可与上传并行 |
| 融合 + digest | 本地 | 秒级 | 规则 + 模板 |
| **default 模式合计** | | **约 4–6 分钟** | 可接受；异步任务 |
| All-In-One 段落 | 本地 | 10–30 分钟 | 可选；不要默认 |
| Demucs 分离 + 歌词 | 本地 | 30–90 分钟 | 只对音乐段/歌曲做 |
| Omni 旁白 | 云端 | 30–90 秒/10 段 | 只对选中窗口 |

### 7.2 本地依赖与跨机器 RTF

- **不要分发 PyTorch**。Beat This! 已有 ONNX/CoreML 导出（int8 约 20–23MB，精度几乎不掉）；PANNs 可导出 ONNX。发布形态：`ffmpeg + onnxruntime + 2 个小模型 + Python 薄层`。
- 这样 Windows/Mac/Linux 的本地 RTF 才稳定；否则「用户电脑有没有 GPU/torch」会变成支持地狱。
- Qwen 永远走云端，保证重活不落在用户机器上；本地只做「几十 MB 的测量」。
- 首次运行只下载模型（约 30–100MB），不做 2GB 级安装。

### 7.3 缓存与增量

- key = `sha256(file) + pipeline_version + params`；重复分析直接读 gzip。
- 分段缓存：Qwen 按文件、Beat This! 按文件、PANNs 按 10s 窗口；改一个层不重跑其他层。
- `manifest.json` 记录每层的模型版本、耗时、token 用量，便于回归和排查。

---

## 8. 风险与边界

| 风险 | 说明 | 对策 |
|---|---|---|
| AudioFM 不可用 | 论文无权重/API | 默认 BEATs Strong；PANNs 仅 fallback |
| 短音频说话人塌陷 | Qwen <90s 可能全判 S0 | 加 `speaker_confidence=low`；或短音频只给匿名轮次 |
| 歌声/歌词转写差 | 歌曲段文本与对话差异大 | Demucs 分人声 + 单独 `lyrics` 通道；官方歌词优先 |
| 节拍漂移 | 现场/自由节奏/弱起音 | `final0` + 全曲/自适应窗口；标 `beat_confidence` |
| 事件漏检/误检 | 重叠、低能量、罕见类 | 阈值/中值滤波 + `uncertain`；不要硬报 |
| JSON 过大 | 1 小时词级 + beats 很大 | 多分辨率 + gzip + `context` 查询；digest 不进全量 |
| 模型/API 漂移 | 模型名、参数、价格会变 | `capabilities` 记录版本；`doctor` 自检；失败降级要显式 |
| 依赖地狱 | madmom/NATTEN/torch 在 Mac 上难装 | 默认不带 All-In-One；ONNX 化；可选 extra |
| 过度承诺 | 「正常人听觉」是营销话术 | 文档写清边界：离线、非实时、匿名说话人、复调转谱不支持 |
| 版权/隐私 | 音乐、人声、声纹 | 本地优先、明确告知、不输出身份；不做声纹识别 |

**明确不做**：

- **Live Translation / 实时通话 / 实时理解 / 直播**（只做离线文件；不设计、不评测）；
- **空间声学 / 空间定位 / 多轨空间任务**（不输出方向、距离、空间音频；不评测）；
- 声纹身份识别、情绪诊断、deepfake 检测；
- 复调音乐总谱转写（加强模式也只做单音/钢琴）；
- 用 ASR 文本冒充「歌词真值」；
- 把 omni 的散文当精确时间戳。

---

## 9. MVP 路线图

### Phase 0（2–3 天）：把「可读」跑通

- `ffprobe` + 响度 + VAD + 10 秒 probe；
- Qwen filetrans 客户端（复用 `ft.py` 的 TOS/oss 上传、submit/poll）；
- `audio-score` schema v0 + `hearing.md` 模板；
- `agent-ear listen --mode default` 输出 gzip + digest；
- 用 5 段素材试：播客、vlog、歌回、游戏、会议。

**验收**：1 小时音频 6 分钟内出 L0/L1；LM 能只读 digest 回答「这段大概是什么、哪几个时间点值得看」。

### Phase 1（3–5 天）：把「可剪辑」跑通

- Beat This! small0（先 PyTorch，后 ONNX）；
- PretrainedSED BEATs Strong（40ms，447 类）+ 后处理；PANNs 仅 fallback；
- 融合关系：`after/over/at/cut_candidate`；
- `ear find` / `ear context` / `ear beats --format edl`；
- 用一段真实视频做「卡点混剪」和「笑声找点」两个 demo。

**验收**：给定 10 个「找笑声/找副歌/找静音」的问题，时间定位误差中位数 < 0.5s；卡点 EDL 可直接被 ffmpeg 执行。

### Phase 2（1 周）：把「像人」跑通

- All-In-One 段落（可选，music 模式）；
- Demucs 人声分离 + 歌词通道（music 模式）；
- Omni 语义旁白（只对选中窗口）；
- 30 段素材的「人类听觉」评测集；
- Skill 打包（SKILL.md + references + doctor）。

**验收**：联合问答（发生了什么/谁/何时/和音乐什么关系）达到人工 baseline 的 80% 以上；幻觉率低于 5%（不确定要标）。

### Phase 3（可选）：跨宿主与生成闭环

- 适配 Claude Code / Codex / DSH / Gemini CLI 的调用方式；
- 生成模型批评回路 demo（TTS 漏字、视频音效不同步）；
- ONNX/CoreML 分发，Windows/Linux 冒烟。

---

## 10. 待确认

1. **AudioFM 具体指哪个？** 公开论文（无权重）、NVIDIA Audio Flamingo 3（数 B 级、NC）、还是某个内部/第三方 API？这决定事件层选型。
2. **宿主范围**：只做 DSH/Claude Code，还是也要 Codex/Gemini CLI？影响工具接口和文件协议。
3. **视频耦合**：不做视频帧/镜头映射，也不做影视模式；只处理音频/视频文件中的音频轨。
4. **输出语言**：中文、英文，还是跟随源语言/双语？
5. **单文件上限**：1 小时、3 小时、还是整场直播？影响分段和成本策略。
6. **music 模式的边界**：音乐转谱、声纹、情绪诊断，哪些要，哪些明确不做？

---

## 附：一句话总结给未来的自己

> 不要把这件事做成「ASR + 音频标签 + BPM 三个 API 的拼盘」。要做成「一条时间轴上的证据图谱 + 一个会问问题的耳朵」：Qwen 听人话，BEATs 听世界，Beat This! 听节拍，融合层听关系。LM 不需要变成 audio-native，它只需要拿到一份**可信、可查、可下刀**的听觉记录。
