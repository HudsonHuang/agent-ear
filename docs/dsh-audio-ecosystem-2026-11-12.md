# DSH 音频/视频生态调研：agent-ear 应该往哪走

> 2026-11-12。范围：DeepSeek Harness 生态里的音频、音乐、视频理解、DAW 相关项目。
> 数据：GitHub stars / npm 周下载 / 公开 README；不是官方统计，只作方向判断。

## 0. 一句话结论

**DSH 里“能听”的东西不少，但“能把声音变成可执行时间轴”的很少；音频-only 项目都很小，真正有量的是“视频理解 + 轻量工具”。**

所以 agent-ear 的触达路径不是“再发一个音频 skill”，而是：

1. 做 **DSH plugin wrapper**（进插件市场，拿到分发）；
2. 做 **视频理解/DAW 的音频层**（挂到已有大流量项目上）；
3. 把输出从“时间戳”升级成“可执行结果”（EDL/SRT/高光/对比报告）；
4. 用真实请求数据决定下一步，而不是继续猜。

---

## 1. 生态里到底有什么

### 1.1 有量的项目（npm 周下载 / stars）

| 项目 | 周下载 | Stars | 它做什么 | 音频部分 |
|---|---:|---:|---|---|
| [dsh-video-storyboard](https://github.com/SAOS-3624/dsh-video-storyboard) | **12,280** | 521 | 视频 → 分镜图 + 带时间码文本 | 只有 transcript + audio envelope |
| [dsh-video-understand](https://github.com/ilps2/dsh-video-understand) | **1,067** | 15 | 视频 → ASR+场景+轨迹+YOLO 信息层 | 只有 ASR |
| [dsh-audio-tools](https://github.com/Ren-xing/dsh-audio-tools) | **827** | 0 | ffmpeg probe/convert/transcribe | 转写 + SRT，无理解 |
| [dsh-video-lens](https://github.com/dundunhan/dsh-video-lens) | **660** | 112 | 视频 → 场景抽帧 + 可选 ASR + VQA | 只有可选 ASR |
| [dsh-tingdong](https://github.com/aicivilization/dsh-tingdong) | **277** | 0 | 英文有声书 → 听力课 | 句子级转写 + 点读 |
| [dsh-soundtry](https://github.com/CixiSVesper/dsh-soundtry) | 未发布 npm | 28 | 本地音乐六件套：转写/节奏/旋律/和弦/结构 | **强**，但 Windows-only、2.4GB |
| [dsh-soundcheck](https://github.com/ALittleLov/dsh-soundcheck) | 未发布 npm | 28 | 本地音乐证据引擎：速度/调性/响度/频段/结构 | **强**，Windows 主验证 |
| [dsh-music-analyze](https://github.com/MukiyoU/dsh-music-analyze) | 未发布 npm | 7 | 音频 → 四张图 + 数字 | 音乐可视化 |
| [dsh-qwen-mm-plugins](https://github.com/ShuiHan268/dsh-qwen-mm-plugins) | 未发布 npm | 4 | Qwen 多模态 12 工具（ASR/AV caption 等） | 原始 API 工具 |
| [dsh-media-tools](https://github.com/averyjohnkucan-arch/dsh-media-tools) | 未发布 npm | 0 | 音频 plot/编辑 + 视频 | 重，Linux/CUDA 21GB Omni |
| [ai-daw](https://github.com/heshengtao/ai-daw) | — | 5 | AI 原生 DAW + MCP/Skill | **没有感知闭环** |
| [dsh-synthv-studio](https://github.com/Making-acid/dsh-synthv-studio) | — | 1 | SynthV 2 Pro 的 DSH 桥 | 无音频评估 |

### 1.2 关键观察

1. **视频项目有量，音频项目很小。** 视频-storyboard 12k/周，音频-only 项目 0–28 stars。
2. **视频项目的音频层都很薄。** storyboard 只有 transcript + envelope；video-lens 只有可选 ASR；video-understand 只有 ASR。**非语音 audio 是空白。**
3. **本地音乐项目很强，但很重、很 Windows。** soundtry 2.4GB/6GB RAM；soundcheck Windows 主验证；media-tools Linux/CUDA。跨平台、轻量、云+本地混合的定位没人占。
4. **DAW 明确缺“自我感知”。** AI DAW README 自己写：模型能生成，但“没有办法注意到自己上一次改动让结果变差了”。这是 agent-ear 最好的新场景。
5. **工具型项目使用量高于“理解型”项目。** audio-tools 827/周、video-understand 1067/周；说明用户先要“能跑、能出字幕/信息”，再谈深度理解。

---

## 2. 竞品弱点：它们怎么感知音频

### 2.1 本地音乐分析（soundtry / soundcheck / music-analyze）

**强项**

- 完全本地、零 API；
- 音乐维度深：BPM、调性、和弦、结构、分轨、旋律；
- 有不确定性/降级说明（soundtry 做得很好）。

**弱点**

- **Windows-only / Windows 主验证**：soundtry 明确 Windows 10/11 x64；soundcheck 也主要 Windows。
- **重**：soundtry 2.4GB、6GB 内存；soundcheck 要装独立 Engine；music-analyze 要 librosa/matplotlib。
- **没有“编辑决策”**：给分析，不给 EDL/SRT/切点偏差/可执行剪辑。
- **音乐强、语音/事件弱**：不是统一时间轴；不做说话人/词级字幕/笑声掌声。
- **与视频工具割裂**：视频 agent 不会自动调用它们。

### 2.2 视频理解（storyboard / lens / understand）

**强项**

- 视觉 token 压缩、场景切分、时间锚定；
- 安装/doctor/失败提示做得比多数音频项目好。

**弱点**

- 音频只被当作“转写”或“能量包络”；
- **没有音乐/事件语义**：不知道哪里是笑声、掌声、玻璃碎、BGM 起落；
- **没有 beat grid/切点**：不能做卡点；
- **没有统一 audio-score**：音频证据和视频证据是两套。

### 2.3 工具型（audio-tools / qwen-mm / media-tools）

- audio-tools：probe/convert/transcribe，解决“能读能转”，不解决“听懂/能剪”。
- qwen-mm：12 个原始多模态工具，模型要自己编排；没有稳定的时间轴/证据 schema。
- media-tools：能力全但重（Linux/CUDA、21GB Omni），不是普通用户默认路径。

---

## 3. agent-ear 的差异化位置

| 维度 | agent-ear | soundtry/soundcheck | video-storyboard/lens | qwen-mm |
|---|---|---|---|---|
| 跨平台 | **macOS/Linux/Windows** | Windows 为主 | 跨平台 | 跨平台 |
| 音频范围 | 语音+事件+音乐 | 音乐为主 | 语音为主 | 原始工具 |
| 统一时间轴 | **audio-score** | 各自报告 | 视频时间轴 | 无 |
| 可执行输出 | 事件/beat/切点 | 分析 | 分镜/字幕 | 原始结果 |
| 云端语义 | **Omni** | 无 | 可选 VLM/ASR | Qwen |
| 本地精修 | BEATs/Beat This! | 本地 | 无 | 无 |
| 安装重量 | basic 轻；precise 可选 | 2.4GB | 中 | 中 |
| 多 agent | Skill（Codex/DSH/Claude） | DSH | DSH | DSH |

**一句话**：

> agent-ear 不是“又一个本地音乐分析器”，也不是“又一个视频分镜器”；它是**跨平台、agent-native、可下刀的音频时间轴层**。

---

## 4. 新的应用场景（按可落地性排序）

### P0：视频的“音频层”

- 给 video-storyboard / video-lens / video-understand 补：
  - 笑声/掌声/玻璃碎/狗叫等事件；
  - BGM 起落、BPM、downbeat；
  - 说话人/词级字幕；
  - 切点偏差。
- 形态：agent-ear 输出 `audio-score`，视频工具把音频时间轴和分镜对齐。
- 这是**最大流量入口**：storyboard 12k/周，audio 是它的明显短板。

### P0：EDL / SRT / 高光导出

用户要的不是 JSON，是“能直接用的东西”：

```bash
agent-ear export .ear/clip --format srt
agent-ear export .ear/clip --format edl
agent-ear highlights .ear/clip --top 5 --by laughter
```

没有导出，用户还要自己写脚本；有导出，才是“剪辑前置工具”。

### P0：DAW 的自我感知闭环

AI DAW 自己承认缺“发现自己改坏了”的能力。闭环：

```text
生成/编辑 → render → agent-ear listen → 指标 JSON
          → 与目标/上一版比较 → agent 调整 → render → ...
```

需要的指标：

- LUFS / true peak / clipping / 动态；
- BPM / 调性 / 段落边界；
- 人声/伴奏比例、频谱平衡；
- 与上一版的差异（响度、低频、峰值、节奏漂移）。

命令缺口：`agent-ear compare a.wav b.wav` / `agent-ear mixcheck`。

### P1：播客/会议/课程

- 章节、说话人时间轴、金句、广告位、可搜索 archive；
- 输出 SRT + chapters + `audio-score`；
- 比“转写”多的是事件/音乐/说话人结构。

### P1：无障碍/SDH

- 词级字幕 + `[laughter]`/`[music]` 非语音提示；
- 这是 agent-ear 已经有、竞品没有的组合。

### P1：流媒体/短视频高光

- 笑声、掌声、能量峰值 + beat + 说话人；
- `highlights` 输出候选片段 + 理由 + 置信度。

### P2：音频资产搜索/记忆

- 把 `audio-score` 当 RAG chunk：按事件/说话人/时间检索；
- “找所有有玻璃碎+人声的片段”。

### P2：现场/工业/安全

- 玻璃碎、警报、枪声、狗叫等事件；注意误报与合规，不做声纹身份。

### P2：教育/有声书

- 句子对齐、章节、发音/语速；tingdong 已验证需求。

### P3：音乐练习/生成 QA

- 音准、节奏、和弦、段落；生成音频的响度/伪影检查。
- 这块 soundtry/soundcheck 更强；agent-ear 应做“时间轴+对比”，不硬拼本地和弦精度。

---

## 5. 用户可能真正要什么（不是时间戳）

时间戳是手段，结果才是需求：

| 用户说 | 真正想要 | agent-ear 应给 |
|---|---|---|
| “把好笑的剪出来” | 高光片段 | `highlights` + EDL |
| “加字幕” | 可直接用的 SRT | `export --format srt` |
| “卡点” | 切点/偏移 | beat grid + `cut_offset_ms` |
| “太吵/太轻” | 混音检查 | LUFS/true peak/频段报告 |
| “这段讲了什么” | 摘要/章节 | hearing.md + chapters |
| “找某个声音” | 搜索 | `find --event/--query` |
| “这个版本比上版好吗” | A/B 对比 | `compare` |
| “视频里发生了什么” | 画面+声音 | 与 storyboard 集成 |

**如果只卖“40ms 时间戳”，受众是剪辑师；如果卖“高光/字幕/混音检查/搜索”，受众是所有人。**

---

## 6. 触达更多人的路径

### 6.1 必做：DSH plugin wrapper

现在 agent-ear 是 **Skill**，不是 DSH **Plugin**：

- Skill 放 `<DSH_HOME>/skills`，不会出现在 DSH 插件市场；
- `awesome-dsh-plugin` / dshmarket / dshbase 要的是 `dsh.bundle.patch` 的 npm plugin；
- 所以 skill-only 的 agent-ear 在 DSH 生态里**没有货架**。

建议做 `dsh-agent-ear` 薄插件：

- 注册工具：`audio_analyze`、`audio_find`、`audio_export`、`audio_compare`；
- 内部调 `agent-ear` CLI；
- 安装时检查/引导 CLI + Qwen Key；
- 附带 skill / prompt section；
- 发布 npm，进 dshmarket / awesome-dsh-plugin / dshbase。

这是**最大的分发杠杆**：插件市场是 DSH 用户实际装东西的地方。

### 6.2 挂到已有大流量项目

- **video-storyboard（12k/周）**：音频层是明显短板；做可选依赖/适配器，或在 README 互相推荐。
- **video-lens / video-understand**：补非语音事件/音乐/beat。
- **AI DAW / SynthV**：做“耳朵/QA” MCP，进入音乐制作闭环。
- **audio-tools**：它是“转写/转换”，agent-ear 是“理解/剪辑”，可以互相推荐，不是竞争。

### 6.3 跨 Agent 分发

- `skills.sh` / Claude Code / Codex：同一份 `skills/agent-ear`。
- GitHub topics：`dsh-skill`、`agent-skills`、`audio`、`video-editing`；**不要**打 `dsh-plugin`，除非真的有 plugin。
- README 首屏：安装命令 + 90 秒 demo + “能剪”的一句话。

### 6.4 内容与社区

- 不发“音频理解”泛科普；发“我测出 QA 打不过 Omni，于是改卖切点”的负结果。
- Demo 只演示一个动作：**切点比 downbeat 晚 180ms，拖回去对上**。
- 目标不是 star，是 3 个真实用户：剪辑师、播客/会议、AI DAW 用户各一个。

---

## 7. 迭代反馈：怎么知道该做什么

不要继续猜“用户要不要时间戳”。做三件事：

1. **本地 intent 日志（opt-in）**：记录 `--request` 的 intent/labels/耗时/错误码，不记录音频内容；聚合后看用户到底要“高光/字幕/卡点/总结/搜索”哪类。
2. **5 个用户访谈**：剪辑、播客、DAW、视频理解、无障碍各 1 个；问“上一次你为了找一个声音/切一个点，实际做了什么”。
3. **激活漏斗**：install → doctor key → 第一次成功分析 → 第一次导出。现在最容易断的是 install 和 key，不是算法。

指标建议：

- 安装成功率；
- 首次成功分析时间；
- 每用户每周分析次数；
- `export` / `highlights` / `compare` 使用比例；
- 30 天留存；
- 失败原因 Top 5（缺 key、ffmpeg、模型、超时、格式）。

---

## 8. 建议的下一步（按 ROI）

1. **`dsh-agent-ear` 插件 wrapper**（分发 + 工具化）。
2. **`export srt/edl` + `highlights`**（把时间轴变成结果）。
3. **`compare` / `mixcheck`**（DAW 闭环）。
4. **video-storyboard 音频适配**（借 12k/周流量）。
5. **intent 日志 + 5 个访谈**（决定要不要做音乐深度/转谱）。
6. 再考虑：本地离线模式、MOSS、转谱。

**不要先做**：更多模型、更多音频类别、更多 benchmark。现在缺的不是“听得更准”，是“用户装得上、用得到结果、愿意第二次用”。

---

## 9. 参考

- [dsh-video-storyboard](https://github.com/SAOS-3624/dsh-video-storyboard)
- [dsh-video-lens](https://github.com/dundunhan/dsh-video-lens)
- [dsh-video-understand](https://github.com/ilps2/dsh-video-understand)
- [dsh-audio-tools](https://github.com/Ren-xing/dsh-audio-tools)
- [dsh-soundtry](https://github.com/CixiSVesper/dsh-soundtry)
- [dsh-soundcheck](https://github.com/ALittleLov/dsh-soundcheck)
- [dsh-music-analyze](https://github.com/MukiyoU/dsh-music-analyze)
- [dsh-qwen-mm-plugins](https://github.com/ShuiHan268/dsh-qwen-mm-plugins)
- [dsh-media-tools](https://github.com/averyjohnkucan-arch/dsh-media-tools)
- [ai-daw](https://github.com/heshengtao/ai-daw)
- [dsh-synthv-studio](https://github.com/Making-acid/dsh-synthv-studio)
- npm downloads API：`https://api.npmjs.org/downloads/point/last-week/<pkg>`
