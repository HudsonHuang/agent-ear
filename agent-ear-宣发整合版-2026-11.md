# agent-ear 宣发整合版（2026-11-11）

> 这是对外宣发的**唯一事实源**。旧的 `ear-宣发准备包.md`、`ear-宣发策略-2026-11.md`、`AEO-策略-2026-11.md`、`agent-ear-干净安装验证-2026-11-11.md` 是过程材料；冲突时以本文为准。
>
> 当前发布：`agent-ear 0.2.4`（PyPI / GitHub）。Windows + DSH 已实际安装测试，PR #1 已合并。

---

## 0. 一页速览

- **它是什么**：给已录好的音频/视频生成**可下刀的时间轴**——不是“再做一个音频问答模型”。
- **强依赖**：Qwen Omni API（`qwen3.8-omni-flash`）。basic / ask / precise / music 都需要 Key + 网络；只有 `privacy` 不调用 Qwen。precise 还依赖 Qwen ASR。
- **差异化**：40ms 事件边界、词级时间、BPM/downbeat、切点偏差；这些是直接问 Omni 拿不到的。
- **诚实结论**：单问题 QA 直接问 Omni 87.2%，agent-ear 的 QA 58.9%；agent-ear 不是 QA 冠军，价值在**可执行的时间轴**。
- **形态**：CLI + Skill（Codex / DSH / Claude Code），macOS/Linux/Windows 原生。
- **发布**：PyPI `agent-ear==0.2.4`；GitHub `HudsonHuang/agent-ear`；Windows CI 通过。

---

## 1. 定位：别卖“听得懂”，卖“能对着剪”

### 一句话

> **给文本模型一副耳朵：把音视频拆成能直接下刀的时间轴。**

### 三版话术

**A. 技术版（DSH / HN / Reddit）**

> 现在真正干活的主力文本模型——DeepSeek、GPT 文本版——没有音频输入通道，只能先转文字再想象声音。
> agent-ear 把 Qwen Omni、BEATs、Beat This! 打包进一个 Skill：不管基模是哪个，装上就多一副耳朵。
> 但它真正给的不是“听懂了”，是**能对着剪**——笑声 00:12.3–00:14.7、downbeat 在 00:21.22、你的切点晚了 180ms。这些是直接问通用多模态模型拿不到的。

**B. 产品版（B站 / 少数派 / 即刻）**

> 剪片子最烦的不是听一遍，是听第十一遍对时间轴。
> agent-ear 把素材列成表：谁在什么时候说了什么、哪里笑了、鼓点在哪、**你这个切点比鼓点晚了几毫秒**。不用听第十一遍，直接对着表剪。

**C. 一句版（≤40 字）**

> 给文本模型一副耳朵：把音视频拆成能直接下刀的时间轴。

### 30 秒电梯稿

> 主流文本模型听不懂音频，只能先转文字。
> 我做了个 Skill，把音频模型打包进去；但它跟 Omni 那种“给你一段描述”不一样：**它给你切点**——笑声从哪到哪、鼓点在第几毫秒、你的切点差了多少。
> 一小时音频约 4 分钟出结果，约两毛钱一小时。
> 它自带退役条件：等文本模型普遍支持音频了，它就该消失。

### 必须说清“里面调了谁”

> “基模不变，我在外面给它挂了一副耳朵。里面用什么模型是我的事，你用的时候不用管。”

**强依赖必须主动说**，不能藏：

> “basic 走 Qwen Omni API；没有 Key 和网络时只有 privacy 本地降级。它不是完全离线工具。”

### 绝对不能说

- ❌ “提升音频理解能力”“比 Omni 强”——自己的 eval 反证。
- ❌ 暗示基模原生获得音频能力。
- ❌ “替代 ASR / 替代 Omni”。
- ❌ “完全离线 / 本地优先”——basic 需要云。
- ❌ 把 40ms 说成 basic 也有；40ms 只属于 precise。
- ❌ 把 DSH Skill 说成 DSH plugin；Skill 放 `<DSH_HOME>/skills`，不需要 `dsh.bundle.patch`。

---

## 2. 证据卡（可直接贴）

| 项 | 数值 |
|---|---:|
| Omni 单模型 QA（180 条） | **87.2%** |
| 无音频 baseline | 56.7% |
| agent-ear QA（同 180 条） | 58.9% |
| 转录后 + 强文本模型（40 条子集） | 77.5% |
| 直接 ask vs 一次转录+回答（180 条） | 87.2% vs 80.0% |
| 1 小时 basic | **231s，RTF 0.064，¥0.211/音频小时** |
| 5 分钟 precise | **57s，RTF 0.19** |
| 5 分钟“只要笑声” basic / precise | 15.2s / 24.1s；53/65 refine |
| 事件精度 | 40ms（BEATs Strong，447 类） |
| 转写精度 | 词级（Qwen ASR） |
| 180 条总音频 | 1.054 小时 |

**最重要的一句**：  
> **QA 不是 agent-ear 的卖点。** 它的增量是“可下刀的时间轴”；单问题要最高准确率，直接问 Omni。

---

## 3. 安装与 Windows 实测

### 安装

```bash
uv tool install agent-ear
agent-ear setup
```

- 先装 CLI，再装 Skill；skill-only 安装（`npx skills add` / clone）必须补 `uv tool install agent-ear`。
- Setup 会问 Qwen Key（隐藏输入），选 Codex / DSH / Claude。
- Windows 原生：`install.ps1`，PowerShell 5.1+，不需要 WSL。
- Windows 配置：`%APPDATA%\agent-ear\config.json`；Skill：`%USERPROFILE%\.dsh\skills\agent-ear`。

### Windows + DSH 实测发现（PR #1 已合并）

- PowerShell 5.1 通过管道传 Key 会带 `U+FEFF` → 现在清理 BOM/零宽字符再校验。
- `--api-key-stdin` 失败后不再 `input()`（避免 EOFError），直接返回 3。
- Beat tracker 返回空 BPM 时不再覆盖 Omni BPM。
- Windows CI（3.10 / 3.12）通过；PR #1：https://github.com/HudsonHuang/agent-ear/pull/1

### 干净安装验证（macOS / Linux）

- CLI 路径通：`uv tool install` → `doctor` → `setup`。
- skill-only 路径已改善：wrapper 缺 CLI 时打印安装指引并以 127 退出；`doctor` 标 `NO-CLI`。
- `--non-interactive --skip-key` 可只装 Skill，Key 以后补。
- 这三条已由 0.2.2 / 0.2.3 修复；Windows 的 BOM/BPM 由 0.2.4 修复。

---

## 4. AEO / Skill 路由：描述已经够用，别再改

实测（强模型 + 51 个 skill，12 条不提名字的用户 query）：

- 应触发 10 条：**全中**（时间轴、找笑声、卡点、转写带时间、视频总结、点名 Qwen、中性目录）。
- 不应触发 2 条：**全对**（写 ffmpeg 命令、实时打断）。

**结论：**

1. **描述不需要重写**；现有 description 已覆盖用户原话。
2. **不要加 assertive cue**（“必须调用我”）——当前精度 100%，加断言只会拿精度换召回。
3. **真正的开关是安装**：没装进 skill 目录时发现率 0；装上后 12/12。
4. 在 1000 个无关 skill 的大库里可能仍会崩，但那是分发后的环境问题，不是当前文案问题。

所以 AEO 的结论是：**先把安装做对，不要改描述。**

---

## 5. 90 秒 demo 脚本

| 时间 | 画面 | 旁白/字幕 |
|---|---|---|
| 0–8s | 一段带笑声和 BGM 的短视频 | “这段素材我要卡点，但不知道鼓点在哪。” |
| 8–18s | 终端：`agent-ear listen clip.mp4 --mode precise --need transcript,events,beat` | “让 agent-ear 听一遍。” |
| 18–30s | 进度/耗时 | “5 分钟素材，57 秒出结果。” |
| 30–55s | `hearing.md` 滚动，高亮笑声、downbeat、切点 | “谁在说、哪笑了、鼓点在哪。” |
| 55–75s | 停在“切点比 downbeat 晚 180ms” | **“这个 180ms，人耳能听出来。”** |
| 75–90s | 剪辑软件里把切点前移 180ms | “现在对上了。” |

关键：第 55–75 秒的 180ms 是全片唯一高光，不要剪掉。

---

## 6. 生态调研结论（2026-11-12）

- DSH 里有量的音频相关项目：`dsh-video-storyboard`（npm **12,280/周**，521★）、`dsh-video-understand`（1,067/周）、`dsh-audio-tools`（827/周）、`dsh-video-lens`（660/周）。
- 音频-only 项目都很小：`dsh-soundtry` / `dsh-soundcheck` 各 28★，且 Windows 为主、2.4GB 级；`dsh-music-analyze` 7★。
- 视频项目的音频层很薄：只有 transcript / audio envelope / 可选 ASR；**非语音事件、音乐、beat、切点没人做**。
- AI DAW 明确缺“发现自己改坏了”的闭环；这是 agent-ear 最好的新场景。
- 最大的分发缺口：agent-ear 是 **Skill**，不在 DSH 插件市场；需要 `dsh-agent-ear` 薄插件（`dsh.bundle.patch`）才能进 dshmarket / awesome-dsh-plugin。
- 详见 [DSH 音频/视频生态调研](docs/dsh-audio-ecosystem-2026-11-12.md)。

## 7. 渠道顺序（简要）

1. **GitHub 本身**：README 前三屏、LICENSE、topic、release。
2. **DSH 生态**：Skill 放 `<DSH_HOME>/skills`；不要投 `dsh plugin add` 渠道（除非另做 plugin）。
3. **skills.sh / Claude Code skill**：`skills/agent-ear/SKILL.md` 自动索引；Claude 用 `~/.claude/skills/agent-ear`。
4. **技术长文 / 视频**：负结果叙事（“我测出它不需要耳朵，于是改卖切点”）。
5. **海外**：Show HN / Reddit 放后面；网络和账号成本高。

**不要**把 agent-ear 投到要求 `dsh.bundle.patch` 的 plugin 目录；它是 Skill，不是 plugin。

---

## 8. 发布前检查清单

- [x] PyPI `agent-ear` 可安装
- [x] GitHub repo / release
- [x] Codex / DSH / Claude 安装
- [x] Windows 原生 CI + PR #1
- [x] Qwen Omni 强依赖写在 README / SKILL / PyPI
- [x] 负结果、成本、RTF 数字
- [ ] 90 秒 demo（仍缺）
- [ ] 一张对比图 / 架构图（仍缺）
- [ ] 一条实测的长视频 demo（1h 已测但无公开素材）
- [ ] 真实用户反馈（目标 3 个）

---

## 9. 仍存在的问题

- 1 小时 **precise** 未实测；只测过 5 分钟 precise。
- 事件 refine 只覆盖可映射标签（主要是 Laughter）；开放标签仍是 `omni-coarse`。
- Qwen diarization 在长音频会过切说话人；需要 `--speakers` 或合并。
- 音乐转谱暂不做；当前音乐层是 Omni 描述 + Beat This!。
- Windows 真机已验证安装，但不同 DSH 版本的路径/权限仍需回归。

---

## 10. 结论

> **agent-ear 不跟 Omni 比“听懂”。**  
> 它把“听懂”变成“能剪”：40ms 事件、词级时间、BPM、切点偏差。  
> 单问题直接用 Omni；要时间轴、要批量、要可审计，才用 agent-ear。

这句是整套宣发的锚点。其余文案都围绕它，不要漂移。
