# Roadmap

> 原则：**默认模式先跑通，其他模式只预留 backend 接口，不提前实现。**
> 项目边界：只做离线文件；不做 Live Translation / 实时 / 直播；不做空间声学；不做完整音乐总谱。

## v0.1 默认模式 MVP（当前）

- Probe/VAD + Qwen Audio 3.1 filetrans + PretrainedSED BEATs Strong（40ms）+ Beat This! small0 + Fusion；PANNs 仅 fallback。
- `audio-score.json` + `hearing.md` + `digest.md`。
- CLI：`probe / listen / digest / doctor / schema`。
- 门控：有语音才 ASR，有音乐才 beat；缺模型/缺 key 显式 warning。
- 评估：MMAU-Pro 150（单文件非空间）+ CMDAR 80 + 内部剪辑 10。

**完成定义**：60s ≤90s、1h ≤10min；schema 通过；3 段真实素材可读；测试全绿。

## v0.2 音乐模式

**输入**：歌曲、BGM、MV、现场。

**本地栈**：
- Demucs stems（MIT）；
- Beat This! beats/downbeats（MIT）；
- All-In-One sections（MIT）；
- basic-pitch 人声旋律（Apache-2.0）；
- 可选和弦：Music.ai（$0.04/min）或本地 chroma/madmom。

**可选 API**：
- **Mirelo Audio-to-MIDI Pro**：唯一自助的 full-mix → per-instrument MIDI；先 10 首歌 eval；
- **Klangio**：单乐器 MIDI/MusicXML；
- **Music.ai**：和弦/节拍/段落/歌词模块。

**输出**：以音乐轴为核心：
- Global：genre / style / language / topic；
- Section：timestamp / instrumentation / musical basis（meter/BPM/key）/ vocal / lyrics；
- 可选：per-stem MIDI 草图、人声旋律 MIDI。

**边界**：
- 不承诺完整乐队总谱/notation-grade；
- 16GB+，约 2–3 分钟/首；
- 不 ship YourMT3（GPL-3.0）、Essentia（AGPL/NC）、Chordino（GPL-2.0）。

## v0.3 隐私模式

- MOSS-Transcribe-Diarize 0.9B + 本地 Qwen3-ForcedAligner-0.6B。
- 不调用任何 API；同 schema，`capabilities` 标记 backend。
- MOSS 段级时间；词级靠本地 aligner；不跑 aligner 就只承诺段级。
- 速度约 1× 实时（M5 16GB），显式提示；低配机器只做 beats/events。
- 不做 Live Translation；实时能力另立项目。

## v0.4 Agent 集成与复测

- `SKILL.md` 已可用；后续加 `find/context/listen --window`。
- 可选 MCP 包装（Claude Code/Codex/DSH）。
- 复测 API 标准化；跨宿主输出一致。

## v0.5 稳定与分发

- 批量/异步；ONNX/CoreML 分发（不依赖 torch）。
- schema v1 冻结；版本迁移；模型/许可清单。
- 评估集固定，回归门禁（准确率不下降）。

## 非目标（长期）

- Live Translation、实时通话、实时理解、直播。
- 空间声学/空间定位/空间音频。
- 声纹身份、情绪诊断、deepfake 检测。
- 完整音乐总谱/出版级谱。
- **影视模式/视频帧对齐/EDL**：本项目暂不做；只做音频/视频中的音频理解。
