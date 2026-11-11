# 前置判断：现存方案重合度与「还有没有必要做」

> 这份文档只回答三个问题：**有没有人做过？重合在哪？还值不值得做？**
> 结论先行：**有大量相邻方案，但没有同构方案。重合在「转写 / 描述 / 单点编辑」，空白在「跨层融合 + 可移植的音频时间轴 + 三模式路由」。所以有必要，但必须砍掉「通用音频理解」的定位，只做「剪辑与生成闭环的耳朵」。**

---

## 1. 先定「重合」的判断口径

一个 Skill 要覆盖 6 件事，才算和 Ear 同构：

| # | 能力 | 说明 |
|---|---|---|
| A | 吃音频/视频文件 | 不是实时麦克风 |
| B | 语音转写 + 时间戳 | 词级/句级 |
| C | 说话人 / 非语音发声 | 谁在说、笑/叹气/掌声 |
| D | 音乐理解 | BPM、beats/downbeats、段落、歌词 |
| E | 声音事件 | AudioSet 类事件 + 起止时间 |
| F | 跨层融合 + 可执行动作 | 关系、显著性、EDL/剪辑建议 |

**大部分现有方案覆盖 A–C；少数覆盖 D/E；几乎没人覆盖 F。** 这就是取舍的起点。

---

## 2. 现有方案盘点

### 2.1 通用音频 Skill / MCP（最直接的重合）

| 方案 | 覆盖 | 交付形态 | 和 Ear 的重合 | 结论 |
|---|---|---|---|---|
| **`guanzhe-asr-listen`**（OpenClaw Skill，1★） | A–C + 情绪/语气 | 本地 whisper.cpp + 云端 MiMo 路由；TXT/SRT/VTT/LRC/JSON + 词级时间 | **高**：本地/云端路由、隐私边界、歌词/方言、情绪分析，思路几乎一样 | 说明「路由 + 模式」不新颖；但它**没有 D/E/F**，仍是语音 Skill |
| **`watch-skill`**（568★） | A–C，视频为中心 | 时间戳证据库；音频只做字幕 | 中：证据/时间戳理念相同 | 它的音频是「字幕」，不是「听觉」 |
| **`audio-intelligence-mcp`**（1★） | A–E | Whisper + PANNs + VAD + 可选 pyannote，输出 JSON envelope | **最高**：概念上最接近 | 单作者、未验证、无融合语义；说明「组件拼接」不是护城河 |
| **`mimo-agent-skill`**（8★） | A–C | 给 coding agent 的多模态 skill/MCP | 中：宿主集成方式相同 | 偏「调用多模态模型」，不是时间轴 |
| **`fcp-mcp-server`**（PyPI） | A–C + 剪辑动作 | Final Cut Pro XML；静音检测、基于转写的剪辑 | 中高：已经能「用转写剪 FCP」 | 绑定 FCP、无音乐/事件层 |
| **`arkcli-understand` / `bailian-gen`**（你机器上已有） | A–C + 视频理解 | `vau`、`asr`、`asr-speakers`、`bl speech recognize` | **高**：转写/说话人/音视频描述都能做 | 不能给 beat grid/事件时间轴/EDL |
| **商业音频智能 API**（ElevenLabs Scribe、AssemblyAI、Deepgram、Speechmatics） | A–C + 部分 D | ASR + diarization + `audio_event`（如笑声/掌声）+ 章节/摘要/情感 | 高：语音层已经商品化 | 不做音乐节拍/跨层融合；多为「语音 + 少量事件」 |
| Anthropic 官方 skills | 文档/表格/PPT/PDF | 19 个 | 无音频 | 官方没做，不代表不能做；但说明不是「标配」 |

**关键判断**：**「又一个音频 Skill」这个位置已经很挤，而且大部分是 Whisper 包装。** 如果你只做「转写 + 总结 + 字幕」，这个 Skill 没有必要——直接用 `arkcli-understand` / `bailian-gen` / `guanzhe-asr-listen` 更省事。

### 2.2 视频编辑产品 / Agent（场景上的重合）

| 方案 | 已经做到的 | 是否 agent 可调用 | 和 Ear 的重合 |
|---|---|---|---|
| **Descript API + MCP** | 导入素材，用自然语言让 Underlord 去口癖、修音、加字幕、剪短视频；有 MCP，可在 Claude/ChatGPT/Codex/Cursor 里用 | **是** | **高**：它就是一个「会剪视频的 agent」 |
| **OpusClip MCP** | 37 个工具：提交项目、拿 clip、拿 transcript、分析画面、发布；有 Claude Connector 和 Skill | **是** | 高：自动切片/剪辑，但**从工具目录看没有 beat/事件时间轴** |
| **CapCut / Premiere / DaVinci** | 自动卡点、静音删除、自动字幕、音频增强 | 否（消费级 UI/插件为主） | 产品级高，agent 级低 |
| **iZotope RX / Adobe Enhance** | 降噪、修复、响度 | 否 | 信号层高，理解层低 |

**关键判断**：**「AI 剪视频」这个产品位置已经被 Descript/OpusClip/CapCut 占了。** 不要做另一个编辑器；要做它们**不提供的、可移植的音频理解层**。Descript/OpusClip 虽然已经有 API/MCP，但它们是**绑定各自工作流**的：Descript 的编辑发生在 Descript 项目里，OpusClip 的产物是它自己的 clip；你很难把它们的「听觉」抽出来，变成一份通用 `audio-score` 喂给另一个 NLE 或另一个 LM。**可编程 ≠ 可移植**，这正是 Ear 的空间。

### 2.2b Agent-native 剪辑工具：actuator 很多，sensor 很少

2026 年真正成熟的 agent 视频工具，几乎全是「执行器」（帮我切/渲染/导出），不是「感受器」（告诉我听到了什么）：

| 工具 | 能力 | 性质 |
|---|---|---|
| **`ffmpeg-skill`**（5.0k★） | 42 个 FFmpeg 工具 + MCP，机器可读契约 | 执行器；不理解音频内容 |
| **`Concat`**（16.5k★） | JSON-RPC 编辑 API | 执行器 |
| **`OpenChatCut`**（3.0k★） | 词级转写剪辑、auto-ducking、FCPXML | 执行器；转写是输入，不是证据层 |
| **`ChatCut agent-plugin`**（1.0k★） | MCP；beat-synced cuts 标注为 Desktop，MCP 调不到 | 执行器；卡点是功能，不是证据 |
| **`cartcut`**（830★）/ **`FableCut`**（790★） | JSON timeline / MCP+REST | 执行器 |
| **Premiere Pro MCP**（847★） | 通过 UXP/CEP 操作时间线、markers | 执行器；markers 需要别人给 beat |
| **`claud-ear`**（1★） | CLAP embeddings + beat **generation** | 最接近「耳朵」，但极小、偏生成 |
| **AssemblyAI MCP**（1★）/ **`qwen-omni-mcp`**（2★） | ASR / omni 封装 | 语音层，不是融合层 |

**关键判断**：**生态是「actuator-heavy, sensor-light」。** 你能找到一堆帮你「切」的工具，但找不到一个能回答「三个最大的笑声在哪、音乐在不在下面、小节网格是什么」的可查询对象。**这就是 Ear 的位置：actuator 上游的 sensor/evidence compiler，而不是另一个 actuator。**

### 2.3 音乐模式：多轨转谱 API 没有想象中多

你之前说「暂时没看到音乐多轨转谱 API」——**有，但只有一家是自助的**，而且质量还没被第三方验证：

| 服务 | 能力 | 输出 | 接入/价格 | 结论 |
|---|---|---|---|---|
| **Mirelo Audio-to-MIDI Pro** | 整首歌 → **每件检测到的乐器一条 MIDI** + note events（pitch/time/velocity/instrument）+ tempo/meter + MusicXML（key/chord） | MIDI / MusicXML / PDF（可选） | 自助 API；30 min / 100 MiB；同步端点 ≤12 min；$0/$20/$100/$300/$1000/月 | **唯一自助 full-mix 多轨转录**；准确率无第三方 benchmark，必须先用 10 首歌 eval |
| **Songscription** | Multi-Instrument：keys/guitars/bass/strings/brass/woodwinds/sax/synths/voice/drums → MIDI/MusicXML/PDF/GP5 | 谱面/MIDI | 消费级 SaaS；**API 仅 Enterprise**；Plus/Pro 单次 ≤15 min | 能力强，但不是自助 API；厂商声称，未审计 |
| **Klangio API** | **单乐器**转写（piano/guitar/bass/drums/vocal/violin/wind）+ 源分离 + beat/BPM/meter + 和弦 + 扫弦 | MIDI / MusicXML / PDF / GP5 | 申请制；$0/50 次/15s；$99/500 次（≤300s）；$499/3000；Ent ≤600s | **不是 full-mix 多轨**；适合「给我钢琴/吉他/人声这一轨」 |
| **Music.ai（Moises）** | 模块化：chords $0.04/min、beats $0.03、sections $0.04、lyrics $0.17、word align $0.09、instruments $0.02、vocal pitch $0.05、Cyanite $0.15、stems $0.07 | JSON/音频 | 公开 API | 适合「和弦/节拍/段落/歌词」，**没有 per-instrument MIDI** |
| **AudioShake** | stems（鼓 6 路、吉他 ac/el、keys、piano、strings、wind）+ lyrics 词级对齐 + 音乐检测 | 音频/文本 | API + 本地 SDK（macOS ARM） | 强在分离/歌词，**不给 MIDI** |
| **LALAL.AI** | stems + denoise | 音频 | quote | 不做转录 |
| **Melodyne / AnthemScore / Chordify** | 桌面/网页 | — | 无公开 API | 不能作为 Skill 依赖 |

**本地替代**：

- Demucs（MIT）：stems；
- basic-pitch（Apache-2.0）：单音/钢琴/旋律 note events；
- Beat This!（MIT）：beats/downbeats；
- All-In-One（MIT）：段落 + 标签；
- MT3（Apache-2.0）：多乐器，TF1 时代，重；
- **不要 ship**：YourMT3（GPL-3.0）、Essentia（AGPLv3 + CC-BY-NC-SA 模型）、Chordino（GPL-2.0）；和弦可用 madmom（BSD-3，但 Python ≤3.10 麻烦）或 librosa chroma（ISC）。

**结论**：**音乐模式不要自研转谱引擎。** 本地做「stems + beats + sections + 歌词 + 人声旋律 MIDI」，需要 full-mix 多轨 MIDI 时接 **Mirelo**（先 eval），或单轨接 Klangio。承诺边界：**「近似和弦/段落/调性/速度/人声旋律」可以，「完整乐队总谱/出版级谱」不行。**

### 2.4 统一 omni 模型（能力上的重合）

| 方案 | 能做的 | 不能做的 |
|---|---|---|
| Gemini / Qwen-Omni / GPT-audio | 描述场景、情绪、大致内容；可做语义旁白 | 精确 beat grid、word-level 时间、事件 onset、可靠 diarization |
| Audio Flamingo 3 | 音频理解强，10 分钟级 | 非商用许可、无时间戳、不是小模型 |
| AudioFM（论文） | 自监督表示 SOTA | 无公开权重/API，不能落地 |

**结论**：omni 是「语义旁白/路由」，不是「测量仪」。Ear 不跟它抢「描述」，只补「时间 + 关系 + 可执行」。

---

## 3. 重合度矩阵：到底哪里是空白

| 层 | 现有覆盖 | 重合度 | 建议 |
|---|---|---|---|
| 语音转写 / 说话人 | Qwen、Whisper、MiMo、arkcli、bailian、ElevenLabs、AssemblyAI | **90%** | **不要自研**；包成 backend |
| 非语音事件 | BEATs Strong/PANNs、AudioSet、ElevenLabs `audio_event`、AudioShake | 60% | 用组件 + 后处理，价值在「时间定位 + 融合」 |
| 音乐基础（BPM/beats） | Beat This!、All-In-One、librosa、Klangio、Music.ai | 70% | 用组件；downbeat 是差异点 |
| 音乐转谱 | Mirelo（full-mix）、Songscription（企业）、Klangio（单轨）、basic-pitch、MT3 | 60% | **接 API/本地模型，不自研** |
| 跨层融合 / 关系 / 显著性 | 几乎没有成熟方案 | **10%** | **主战场** |
| 可移植的剪辑动作（EDL/XML/SDH） | FCP MCP、Descript/Opus 封闭工作流 | 25% | **主战场**：跨 NLE、可解释 |
| 多模式路由（质量/隐私/音乐） | `guanzhe-asr-listen` 有本地/云端路由 | 40% | 模式不新颖，但「三模式 + 同一 schema」是差异 |

**一句话**：**底层全是商品，中间层是空白。** 你的设计如果停留在「把 Qwen/PANNs/Beat This! 串起来」，重合度很高；如果落在「融合 + 可移植动作 + 模式策略」，重合度很低。

### 重合度结论（粗略但可用）

| 你的做法 | 与现有方案的重合度 | 判断 |
|---|---|---|
| 只做「转写 + 音频标签 + BPM」 | **80–90%** | 不建议做；直接用现成 Skill/API |
| 做「转写 + 标签 + BPM + 一个漂亮 JSON」 | 60–70% | 仍然危险；JSON 不是护城河 |
| 做「融合关系 + 显著性 + 剪辑动词 + 三模式」 | **20–30%** | 值得做；这是空白 |
| 做「生成模型的听觉批评回路」 | **<10%** | 最值得做，但最难 |

---

## 4. 取舍：砍什么、留什么

### 必须砍掉（否则就是重复造轮子）

1. **通用转写/字幕工具**：`arkcli-understand`、`bailian-gen`、Whisper MCP 已经够好；Ear 只把转写当输入。
2. **通用「和音频聊天」**：omni 模型直接做，Ear 不做。
3. **完整视频编辑器**：Descript/OpusClip/CapCut 已经占位；Ear 只出 EDL/XML/建议，不碰时间线 UI。
4. **音乐转谱引擎**：Mirelo（full-mix）/Klangio（单轨）/Music.ai（模块）+ 本地模型；Ear 只做路由和结果融合。
5. **声纹身份/情绪诊断**：伦理和准确性都不适合作为默认能力。

### 必须留下（真正的差异化）

1. **统一 `audio-score`**：语音、事件、音乐在同一时钟上，带 `confidence`/`source`/`uncertain`。
2. **关系与显著性**：`after/over/at/cut_candidate`，以及「什么是前景」。
3. **多分辨率 + 可查询**：1 小时音频不塞 6 万 token；`find/context/listen --window`。
4. **剪辑动词**：`beats --format edl`、`find --event Laughter`、`export srt`、`cut_candidate`。
5. **三模式策略**：default / music / privacy，**同一 schema，只换 backend**。
6. **可移植**：任何 LM（Claude/GPT/DeepSeek/Gemini）、任何 NLE（FCP/Premiere/DaVinci/ffmpeg）。

### 定位一句话

> **Ear 不是「音频理解模型」，是「把音频编译成可编辑、可审计的时间轴」。它站在 ASR/omni/编辑器和 LLM 之间。**

---

## 5. 还有没有必要？用三个测试判断

### 测试 1：拿掉融合层，它还剩下什么？

如果拿掉 `relations`、`salience`、`cut_candidate`、多分辨率，Ear 就退化成「Qwen + PANNs + Beat This! 的拼盘」，和 `audio-intelligence-mcp` / `guanzhe-asr-listen` 高度重合。**融合层是必要性的唯一证明。**

### 测试 2：Descript/OpusClip 能不能替代？

- 「去口癖、加字幕、切短视频」→ **能**，不要竞争。
- 「在我的 NLE 里，按我的风格卡点，并解释为什么这一刀晚了 180ms」→ **不能**。它们是绑定自己工作流的编辑助手，不给你一份可移植、可解释的音频证据。
- 「让生成模型听自己的输出并自我修正」→ **不能**。它们不提供「批评 API」。

### 测试 3：宿主模型原生能不能做？

- Claude Code：不能听（Read 不支持音频）→ 需要 Ear。
- Codex：有条件传音频，但输出散文，没有 beat/event 时间轴 → 需要 Ear 的结构化层。
- Gemini：能听，但时间戳漂、没有 beat grid → 需要 Ear 的测量层。
- DeepSeek/本地文本模型：不能听 → 需要 Ear。

**结论**：

- **有必要**：面向「剪辑 + 生成自修正 + 跨模型/跨 NLE」。
- **没必要**：面向「转写、总结、通用音频问答、消费级自动切片」。
- **判断标准**：列出 10 个「现有 Skill 做不到、Ear 能做到」的任务；如果少于 5 个，停。

### 10 个「只有 Ear 能做」的候选任务

1. 在任意 NLE 里按 downbeat 卡点，输出可执行 EDL，并解释哪一刀偏了。
2. 3 小时直播里按「笑声/掌声/突然安静」找高光，带前后语音上下文。
3. SDH 字幕：非语音事件 + 说话人 + 时间，而不是只有台词。
4. 检测「音画不同步」：爆炸音效比画面冲击晚 0.4 秒。
5. 给生成视频做音频批评：环境声断层、音乐情绪不对、静音突兀。
6. 配音/译制 QA：双边词级时间轴，找漏句/超长/口型。
7. 播客：章节 + 广告口播 + 音乐床 + 静音 + 口头禅。
8. MV/歌词视频：lyrics + section + beat 三者对齐。
9. 解释「为什么这段剪辑听起来不舒服」：不是给分数，是给证据。
10. 同一份 `audio-score` 被 Claude/GPT/DeepSeek/Gemini 共用，不绑模型。

如果这 10 个里有 5 个以上是你真正要做的，**这个 Skill 值得做**；如果主要是 1/2/7，**先确认 Descript/OpusClip 是否已经够用**。

---

## 6. 三模式设计：同一 schema，不同 backend

| 模式 | 语音 | 事件 | 音乐 | 语义旁白 | 约束 | 目标 |
|---|---|---|---|---|---|---|
| **default** | Qwen Audio 3.1 filetrans（API） | PretrainedSED BEATs Strong（本地，40ms） | Beat This! small0（本地） | 可选 omni | 成本/隐私提示；缓存；按需精听 | 普通人水平，1h ≈ 4–6 min |
| **music** | Qwen（可 API） | BEATs Strong（或 PANNs fallback） | Demucs + Beat This! + All-In-One + basic-pitch；可选 Mirelo（full-mix）/Klangio（单轨）/Music.ai（模块） | 可选 | 需要用户算力；16GB M5 约 2–3 min/首 | 音乐增强，段落/和弦/人声旋律/谱面初稿 |
| **privacy** | **MOSS**（本地，替代 Qwen） | BEATs Strong（或 PANNs fallback） | Beat This! | 禁用 | 不调用任何 API；MOSS ~1× 实时；16GB 起 | 完全本地，慢但可用 |

**关键设计**：模式不是三套产品，而是**同一 `audio-score` 的三种 backend 策略**。这样：

- 默认模式跑通后，music/privacy 只是替换 backend，不改 schema；
- 用户可以在文件级/任务级切换；
- 输出可以 diff：同一段音频，default vs privacy 的差异一目了然。

**模式判定**（按用户提供的背景，而不是写死）：

1. 显式参数优先：`--mode default|music|privacy`。
2. 否则从话术/文件推断：
   - 「不要上传 / 本地 / 隐私 / 不要调用 API」→ **privacy**；
   - 「扒谱 / 分轨 / 和弦 / 编曲 / 音乐分析 / 卡点」→ **music**；
   - 其他 → **default**。
3. 推断结果要写进 `provenance.mode` 和 `warnings`，让用户知道这次用了哪个后端、有没有上传。
4. 推断不确定时，默认 **default**，但在第一次调用 API 前提示「会上传音频」；用户拒绝就切 privacy。

**隐私模式的一个实现细节**：MOSS 输出是**段级** `[start][Sxx]text[end]`，没有词级时间。你项目里的做法是「MOSS 文本 + 本地 Qwen3-ForcedAligner-0.6B」；forced aligner 是本地小模型，不是 ASR API，所以 privacy 模式仍然成立。若不跑 aligner，就只承诺段级时间，并在 `warnings` 里写清楚。**不要把「段级」伪装成「词级」。**

**默认模式的成本/隐私策略**（你要求考虑）：

- 上传前明确提示「音频会发送到 DashScope」；`--no-upload` 自动切 privacy。
- 先 probe：纯音乐/静音/无语音的文件不送 ASR；只对语音段送。
- 缓存：`sha256 + params`，重复分析零成本。
- 预算：`--max-api-minutes`，超限降级到 MOSS 或只做索引。
- 只对候选窗口做深度分析（先索引后精听），不默认全量。

---

## 7. 音乐模式：调研结论与建议

### 7.1 可用的多轨/转谱 API（修正版）

- **Mirelo Audio-to-MIDI Pro**：目前唯一自助的 full-mix → per-instrument MIDI；30 min/100 MiB；同步 ≤12 min；$0/$20/$100/$300/$1000/月；**准确率无第三方 benchmark**，先拿 10 首歌 eval 再决定是否上线。
- **Songscription**：多乐器、输出 MusicXML/PDF/MIDI，但 API 只对 Enterprise 开放；单次 ≤15 min；厂商声称，未审计。
- **Klangio**：单乐器（piano/guitar/bass/drums/vocal/violin/wind）+ separation/beat/chord；**不是 full-mix 多轨**。
- **Music.ai**：按模块买（chords/beats/sections/lyrics/alignment/instruments/vocal pitch/stems），没有 per-instrument MIDI；适合把音乐语义补起来。
- **AudioShake**：stems + lyrics 对齐；有 macOS 本地 SDK，是商业本地分离的替代。

### 7.2 本地替代与许可红线

| 组件 | 许可 | 用途 | 16GB M5 估算 |
|---|---|---|---|
| Demucs htdemucs | MIT | 4/6 stems | 3–5 min 歌约 20–40s（MPS） |
| basic-pitch | Apache-2.0 | 人声/旋律/钢琴 MIDI | 4 stems 约 15–25s |
| Beat This! | MIT | beats/downbeats | 2–5s |
| All-In-One | MIT | sections/labels | 40–90s（最大头） |
| MT3 | Apache-2.0 | 多乐器（重） | 不建议默认 |
| **YourMT3** | **GPL-3.0** | 多乐器 | **不要 ship** |
| **Essentia** | **AGPLv3 + NC 模型** | 和弦/结构 | **不要 ship** |
| **Chordino** | **GPL-2.0** | 和弦 | **不要 ship** |

**端到端**：3–5 分钟歌约 **2–3 分钟**（约 8–12× 实时）；其中 Demucs 是实测，其余是估算。

### 7.3 建议（按优先级）

1. **和弦 + 调性 + BPM**：Music.ai（$0.04/min）或本地 chroma/madmom；性价比最高。
2. **段落标签**：All-In-One；把时间戳变成「intro/verse/chorus」。
3. **歌词 + 词级时间**：有人声时做；Qwen filetrans 或 AudioShake。
4. **人声旋律 MIDI**：basic-pitch 跑 vocals stem；这是最不容易错的一项。
5. **per-stem MIDI（bass/keys/guitar）**：标成「草图」，不承诺准确。
6. **full-mix 多轨 MIDI**：只放 `--music-api mirelo` 后面，先 eval 10 首再加默认。

**不要承诺**：完整乐队总谱、notation-grade 准确率、密集/现场混音的分轨、吉他/贝斯 tab、调式爵士/转调的和弦确定性、rubato 的 tempo map、Melodyne 级编辑。文案写「近似和弦、段落、调性、速度、人声旋律」，不要写「transcription」。

---

## 8. 最终判断

### 8.1 你的设计哪些部分是重合的

- 「调用 ASR + 音频标签 + BPM」→ **高度重合**，市面上有大量组件和 Skill。
- 「本地/云端路由 + 隐私模式」→ **中度重合**，`guanzhe-asr-listen` 已经这么做。
- 「多模态描述 + 总结」→ **高度重合**，omni 模型和 `vau` 已经能做。

### 8.2 哪些部分是空白的

- **先证据、后动作（evidence before action）**：现在的可编程界面要么是「prompt → 不透明 job」（Descript/Underlord），要么是「一个动作一个 tool」（OpusClip/ChatCut）。没有「先问、拿到带置信度的结构化证据、再决定怎么切」的层。
- **跨层融合**：语音/事件/音乐的统一时钟、关系、显著性。
- **可移植的剪辑动作**：EDL/XML/SDH，不绑 NLE、不绑模型。
- **生成模型的听觉批评回路 / 渲染后复测**：切点偏了 80ms、笑声被切掉、ducking 深度不够——没有一个产品把「复测」做成 callable check。
- **三模式同一 schema**：default/music/privacy 可切换、可 diff。

### 8.3 项目边界：不做 Live Translation

本项目只处理**离线文件**。**Live Translation、实时通话、实时理解、直播**是明确的非目标：不设计、不实现、不纳入评估。**空间声学/空间定位/多轨空间任务**同样不做：不输出方向/距离/空间音频，也不纳入评估。未来若要做，另立项目（可能用 MOSS Live），不复用本项目的 schema 承诺。

### 8.4 风险：宿主在往上爬

Descript 和 OpusClip 已经在 ship MCP；如果它们下一步把 **word timings + beat markers + 事件** 暴露出来，转写那一半会快速商品化。**能守住的不是 ASR，也不是 beat detection，而是：融合 + 事件语义 + 置信度 + 复测。** 所以 Ear 要尽早把「`audio-score` + 复测」做成标准，而不是把精力花在接更多模型上。

### 8.3 一句话建议

> **做，但只做「融合层 + 剪辑动词 + 三模式」，不要做「通用音频理解」。**
> 默认模式先落地；music/privacy 只预留 backend 接口，不急着实现。
> 如果拿掉融合层，这个项目就不值得做——因为那时它只是一个更贵的 Whisper。

---

## 附：证据链接

- [guanzhe-asr-listen](https://github.com/2xmncvcx92-dotcom/guanzhe-asr-listen)
- [watch-skill](https://github.com/oxbshw/watch-skill)
- [audio-intelligence-mcp](https://github.com/DNSdecoded/audio-intelligence-mcp)
- [fcp-mcp-server (PyPI)](https://pypi.org/project/fcp-mcp-server/)
- [Descript API](https://help.descript.com/developers) / [Descript MCP](https://help.descript.com/developers/mcp/overview)
- [OpusClip MCP](https://help.opus.pro/api-reference/agent-setup)
- [Klangio API](https://klang.io/api/)
- [Mirelo Audio-to-MIDI Pro](https://mirelo.ai/audio-to-midi)
- [Music.ai SDK](https://www.npmjs.com/package/@music.ai/sdk)
- [AudioShake Developers](https://developer.audioshake.ai/models)
- [PretrainedSED](https://github.com/fschmid56/PretrainedSED) / [Beat This!](https://github.com/CPJKU/beat_this) / [All-In-One](https://github.com/mir-aidj/all-in-one) / [PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn)
- [AudioFM 论文](https://arxiv.org/abs/2610.34183)

> 注：Klangio/Mirelo/Music.ai 的价格和限额可能变动；上线前以官方页面为准。**修正**：Klangio API 是**单乐器**转写（piano/guitar/bass/drums/vocal/violin/wind）+ 分离/节拍/和弦，不是 full-mix 多轨；真正自助的 full-mix → per-instrument MIDI 目前只有 Mirelo，且其准确率无第三方 benchmark，必须先用 10 首歌 eval。Songscription 能力接近但 API 仅 Enterprise。
