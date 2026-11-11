# AED 选型：从 PANNs 换到 PretrainedSED BEATs Strong

> 日期：2026-11-11
> 需求：时间粒度约 100ms（不要求真正逐帧，但必须明显细于 5s）；类别足够多；本地可跑、RTF < 1；尽量现代、端到端，不用 PANNs 那种传统特征。

## 结论

**默认 AED = PretrainedSED `BEATs_strong_1`。**

- 40ms 帧级输出（比 100ms 更细）
- 447 个 AudioSet Strong 类别，直接输出 onset/offset
- BEATs 是端到端音频 spectrogram transformer，不是手工特征
- MIT；checkpoint 364MB
- 60 秒音频推理约 2.5 秒（含加载），RTF ≈ 0.04
- AudioSet Strong PSDS1 **46.5**（论文 Table；同管线高于 ATST-F 45.8、fPaSST 45.4、M2D 46.3、ASiT 46.2）

**PANNs 降级为 fallback**：`--aed panns` 或 BEATs checkpoint 缺失时使用。

## 候选对比

| 模型 | 时间粒度 | 类别 | 端到端/现代 | 许可/权重 | 本机可行性 | 结论 |
|---|---|---|---|---|---|---|
| **PretrainedSED BEATs Strong** | **40ms** | 447 AudioSet Strong | 是，BEATs transformer | MIT，GitHub release 364MB | 60s≈2.5s，RTF 0.04 | **默认** |
| PretrainedSED ATST-F Strong | 40ms | 447 | 是，ATST-Frame | MIT，344MB | 同量级 | 备选；PSDS1 45.8 |
| AudioMosaic ViT-B/16 AS-2M | 160ms patch；clip-level head | 527 | 是，ViT | MIT，~86M | 快 | **不够细**：没有公开帧级 SED 头；SED 探针只有 27.3 frame mAP |
| PANNs CNN14 | 5s 窗口（MVP） | 527 | 否，CNN + 传统 mel | MIT，327MB | 快 | 旧、时序弱；fallback |
| ATST-Frame（DESED 微调） | 40ms | 10 DESED 类 | 是 | 开源 | 快 | onset 强，但类别太少，不适合通用 |
| Audio Flamingo 3 | 无时间戳 | 开放描述 | 是，LLM | CC-BY-NC | 7B 级，重 | 只能做语义旁白 |
| Qwen3-Omni | 文本时间戳，漂移 | 开放 | 是 | 30B-A3B，重 | 16GB 难 | 不做 AED |
| Gemini | 文本时间戳，漂移 | 开放 | 是 | API | 云端 | 不做 AED |

## 为什么不是 AudioMosaic

AudioMosaic 的 AS-2M 头是 **clip-level**（10s 一个 527 类向量），没有公开的帧级 SED 头；论文里的 27.3 frame mAP 是冻结特征 + 线性探针，不是可直接用的强 SED。用它只能 10s/5s 窗口近似，仍解决不了“细粒度事件记录”。BEATs Strong 是专门在 AudioSet Strong 帧级标注上训练的 447 类头，正好补这个缺口。

## 为什么不是 ATST-Frame（单独）

ATST-Frame 的 40ms 和 DESED PSDS1 0.361 很好，但公开微调权重主要是 DESED 10 类；要做通用事件仍然需要 AudioSet Strong 头。PretrainedSED 的 ATST-F Strong 是同一思路的通用版，可作为 BEATs 的备选。

## 解码与后处理

- 模型输出：`(447, T)`，`T = 10s / 40ms = 250` 帧/块；10s 分块，块间无重叠。
- sigmoid → 每类阈值 0.30 → 5 帧 median filter（200ms）→ 合并 ≤120ms 间隙 → 最短 100ms。
- 排除通用层类别：`Speech`、`Music`、`Silence`、`Human voice`、`Conversation`、`Background noise`、`Female/Male/Child speech` 等；这些用于 speech/music ratio，不进入 `events[]`。
- 事件输出：`start_ms`、`end_ms`、`label`、`conf`、`salience`、`source="pretrainedsed-beats-strong"`。

## 已知限制

- 447 类，不是 527；缺少部分细类/音乐风格类。
- 10s 分块无重叠；跨块事件可能被切断。
- 训练数据是 AudioSet Strong（YouTube），对中文/日语语音事件没有专门适配；但事件类别是声音本体，语言影响小于 ASR。
- 阈值/median 需要按素材调；当前 0.30 偏敏感，可在评估后调 0.35–0.40。
- 首次运行需下载 364MB checkpoint；支持 `HTTPS_PROXY`。

## 代码落点

- `ear/aed_psed.py`：subprocess 调 runner。
- `third_party/pretrainedsed/ear_runner.py`：BEATs 推理 + 40ms 解码。
- `ear/cli.py --aed {auto,beats,panns}`：默认 auto（BEATs，失败回退 PANNs）。
- `ear/models.py`：`psed_beats` checkpoint 下载/校验。

## 敞口：AED 不是永久选型

当前默认 **PretrainedSED BEATs Strong** 是 2026-11-11 的快照，不是永久结论。AED 模型迭代很快，Skill 必须允许后来者替换，否则用户会在几个月后拿到次优结果。

### 机制

1. **注册表**：`ear/aed_registry.py` 是唯一选型入口；新增模型只需加一个 provider，不改 fusion/render。
2. **适配器契约**：provider 返回：
   ```json
   {"provider":"...", "events":[{"start_ms":0,"end_ms":100,"label":"Laughter","conf":0.9,"salience":0.8}], "top_labels":[]}
   ```
   帧级/窗口级都接受；`precision` 由 adapter 声明。
3. **安装时检查**：Skill 安装/升级时，agent 应重新查一次：
   - 是否有新的 frame-level SED / audio tagging 模型（AudioSet Strong / DESED / open-vocabulary）；
   - 是否有更好的 40ms 级通用模型；
   - 许可证、权重大小、Mac CPU RTF、是否有官方 eval。
4. **默认不自动切换**：新模型先作为 `--aed <id>` 可选，经过同一批 eval（事件召回/时间误差/RTF）后再改 default。
5. **可回退**：`--aed panns` 保留；`--aed auto` 走 registry 默认。

### 安装时检查清单

- 查 `ear/aed_registry.py` 的 `LAST_REVIEWED`，超过 6 个月视为过期。
- 搜 “audio tagging 2026 frame-level AudioSet Strong / SED / open-vocabulary”；
- 看是否支持 40ms 级输出、447+ 类、MIT/Apache、权重可下载；
- 跑 `agent-ear doctor` 看 registry；跑 `docs/eval-plan.md` 的小集对比；
- 更新 `LAST_REVIEWED` 和 `docs/aed-selection.md`，不要静默改默认。

### 已知候选（未选）

- AudioMosaic：clip-level 527 类，无公开 frame-level head；不作为默认。
- ATST-Frame：40ms 但只有 10 个 DESED 类；不适合通用。
- PANNs：2019，clip-level，作为 fallback。
- 后续可关注：open-vocabulary SED（CLAP/audio-text）、AudioSet Strong 新 SOTA、Better-ASR 附带 event 模型。
