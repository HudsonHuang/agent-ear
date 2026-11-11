# agent-ear

给没有音频通道的文本 Agent 一副**离线耳朵**：把音频/视频编译成同一时间轴上的 `audio-score.json`，再整理成层级化、带时间戳的 `hearing.md`。任何文本模型都能读，不需要模型本身支持音频。

> 状态：**v0.2.4**，PyPI + GitHub 已发布；basic（Omni 详细转录）与 precise（Omni 前置 + 按需精修）已实现。  
> **强依赖：Qwen Omni 模型 API。** basic/ask/precise/music 都依赖 `qwen3.8-omni-flash`；没有 Omni API Key 和网络时，只有 `privacy` 本地降级可用。precise 还额外依赖 Qwen ASR。  
> 边界：只做离线文件；不做 Live Translation、实时流、空间声学、声纹身份、完整音乐总谱。

> **这不是“可选云增强”。** Omni 是基础模式的必需前置；`privacy` 是唯一不调用 Qwen 的模式（MOSS 仍未实现）。

> **配套：实时 vs 离线。** 这个项目处理**已经录好的文件**，给的是可下刀的时间戳。
> 如果你要的是**正在说话时的实时对话、打断（barge-in）**，用 [dsh-moss-live](https://github.com/HudsonHuang/dsh-moss-live)——它管"说得出话"，这里管"切得准"。

## 为什么不是直接问 Omni？

**因为“听懂”和“能剪”不是一回事。**

- 直接问 Omni：180 条 QA **87.2%**；agent-ear 的 QA 只有 58.9%——**它不是 QA 冠军**。
- agent-ear 的增量是 **40ms 事件边界、词级时间、BPM/downbeat、切点偏差**；这些是“能直接对着剪”的东西。

所以：**单问题、只要答案，直接问 Omni；要时间轴/批量/可审计，才用 agent-ear。** 详见 [直接 ask vs 转录后 ask](docs/direct-vs-transcribe.md)。

## 安装

> **DeepSeek Harness 用户**：`dsh plugin add agent-ear` 会装成 bundle（`dsh.bundle.patch` 已在包内），
> 技能会出现在 DSH 的技能目录里。CLI 仍需另外装：`uv tool install agent-ear`。

> **先装 CLI，再装 skill。** `skills/agent-ear/scripts/agent-ear` 只是一个 6 行的薄包装，它 `exec` PATH 里的 `agent-ear` 命令。
> 如果你只用 `npx skills add HudsonHuang/agent-ear`、或手动 clone 来装 skill，**必须另外执行 `uv tool install agent-ear`**，
> 否则第一条命令就会报 `exec: agent-ear: not found`。`agent-ear doctor` 会用 `NO-CLI` 标出这种情况。

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/HudsonHuang/agent-ear/main/install.sh -o /tmp/agent-ear-install.sh
sh /tmp/agent-ear-install.sh
```

或手动：

```bash
uv tool install "agent-ear"          # 只装 basic（推荐先这样）
# uv tool install "agent-ear[local]" # precise 需要：torch/BEATs/Beat This!，体积较大
agent-ear setup
```

### DSH（推荐：npm bundle）

```bash
dsh plugin add agent-ear
uv tool install agent-ear   # CLI 仍需单独装
agent-ear setup --target dsh
```

`agent-ear` 的 npm 包带 `dsh.bundle.patch`，安装后会通过 bundle 注册 Skill；这比手动复制 `<DSH_HOME>/skills/agent-ear` 更容易被 DSH 插件市场发现。

### Windows（原生，PowerShell）

```powershell
winget install Gyan.FFmpeg
uv tool install agent-ear
agent-ear setup
```

如果 GitHub 脚本可用：

```powershell
irm https://raw.githubusercontent.com/HudsonHuang/agent-ear/main/install.ps1 | iex
```

Windows 需要 `ffmpeg`/`ffprobe` 在 PATH；`uv tool install` 默认把 `agent-ear.exe` 放到 `%USERPROFILE%\.local\bin`。
Windows + DSH 已实际安装测试，PR #1 修复了 PowerShell BOM、`--api-key-stdin` 失败提示和 BPM 回退；Windows CI（3.10/3.12）通过。

### 安装向导会问什么

`agent-ear setup` 会：

1. 检查 ffmpeg/ffprobe；
2. 询问 **Qwen API Key**（隐藏输入，不回显）；
3. 可选自定义 base URL（默认 `https://dashscope.aliyuncs.com`）；
4. 检查 Key；
5. 选择要安装的 Agent：Codex / DSH / Claude Code；
6. 写 `~/.config/agent-ear/config.json`（Windows: `%APPDATA%\agent-ear\config.json`，0600）；
7. 安装 Skill，跑 doctor + 本地 smoke test。

Key 也可以走环境变量：`DASHSCOPE_API_KEY`（优先级最高）。

## 快速使用

```bash
# 问答：一次 Omni 调用，同时返回完整分析 + 答案
agent-ear ask input.mp4 "这段音频里发生了什么？"

# 详细转录：完整 transcript/events/music，0.5–2s 时间戳
agent-ear listen input.mp4 --mode basic --out .ear/my-video

# 精确：词级 ASR + 40ms 事件 + beat grid
agent-ear listen input.mp4 --mode precise --need transcript,events,beat --out .ear/my-video-precise

# 长视频只要笑声：不转写，只跑目标事件
agent-ear listen long.mp4 --mode basic --request "把视频里所有笑声都剪出来"
agent-ear listen long.mp4 --mode precise --request "把视频里所有笑声都剪出来"

# 问已保存的转录，不重新调 Omni
agent-ear ask --score .ear/my-video "谁在什么时候笑了？"
```

读结果：

```bash
cat .ear/my-video/hearing.md
agent-ear digest .ear/my-video/audio-score.json --level 1
```

## 输出

```text
.ear/<name>-<hash>/
├── audio-score.json       # 唯一事实源，schema 校验
├── audio-score.json.gz
├── hearing.md             # 层级 Markdown：概览 / 章节 / 音乐 / 事件索引 / 限制
├── digest.md              # 章节级短摘要
├── context.md             # 给文本 LM 的完整上下文
└── work/                  # 16k/32k wav
```

- `audio-score.json`：speech/events/music/relations/timeline/views；事件带 `precision`（`omni-coarse` / `refined-40ms`）。
- `hearing.md`：给 Agent/人读；`# 音频纪要` + `## 概览` / `## 章节` / `## 音乐` / `## 事件索引` / `## 限制`。
- `context.md`：给文本 LM 的完整 transcript/events/music；`agent-ear ask --score` 直接使用，不再调 Omni。

## 模式

| 模式 | 用途 | 时间精度 | 依赖 |
|---|---|---|---|
| `basic`（默认） | 详细转录、摘要、粗剪 | 0.5–2s | Qwen API |
| `precise` | 字幕、打轴、卡点、精剪 | 词级 + 40ms | Qwen + local extra |
| `music` | 音乐描述 + beat grid | BPM/beats | Qwen + local extra |
| `privacy` | 不上传 | 本地 | local extra（MOSS 未实现） |

`precise` 用 `--need transcript,events,beat` 显式指定；不指定时默认三项都跑。`--request` 会按自然语言只跑需要的层。

## 实测（2026-11-11）

| 项 | 结果 |
|---|---:|
| 1 小时 basic 结构化 | 231s，RTF 0.064，¥0.211/音频小时 |
| 5 分钟 precise 全量 | 57s，RTF 0.19 |
| 5 分钟只要笑声 basic / precise | 15.2s / 24.1s；53/65 事件 refine |
| Omni 单模型 QA（180 条） | 87.2% |
| 直接 ask vs 一次转录+回答 | 87.2% vs 80.0%（全量） |
| 转录后强文本模型（40 条子集） | 77.5% |

诚实结论：**basic 的价值是完整转录/时间轴/可审计，不是“QA 超过 Omni”**。单问题最高准确率仍是直接 `ask`；多问题/剪辑才值得先转录。详见 [直接 ask vs 转录后 ask](docs/direct-vs-transcribe.md)。

## Codex / DSH / Claude

安装后 Skill 位置：

- Codex：`$CODEX_HOME/skills/agent-ear`（默认 `~/.codex/skills/agent-ear`）
- DSH：`$DSH_HOME/skills/agent-ear`（默认 `~/.dsh/skills/agent-ear`）
- Claude Code：`~/.claude/skills/agent-ear`

Windows 下对应 `%USERPROFILE%\.codex\skills\agent-ear` 等。

Codex 重启后可用 `/skills` 查看；DSH 新会话可见；Claude 输入 `/agent-ear`。Skill 内部通过 `scripts/agent-ear`（Windows：`scripts\agent-ear.cmd`）调用 CLI。

> DSH 有两种装法：**`dsh plugin add agent-ear`（npm bundle，推荐）**，或手动把 Skill 放到 `<DSH_HOME>/skills/agent-ear`。前者会通过 `dsh.bundle.patch` 注册 Skill，也能进 DSH 插件市场；后者适合不想装 npm 包的用户。

## Doctor / 配置 / 卸载

```bash
agent-ear doctor --json          # 依赖/config/skill/模型，不联网
agent-ear doctor --check-api     # 额外检查 key
agent-ear config show            # 不显示 key
agent-ear config set-key         # 隐藏输入
agent-ear skill list
agent-ear uninstall --target codex
agent-ear uninstall --target all --purge
```

## 已知限制

- basic 是 0.5–2s 时间戳，不能精确打轴；要精确用 precise。
- precise 事件 refine 目前只覆盖可映射标签（如 Laughter）；开放标签仍是 `omni-coarse`。
- 1 小时 basic 已实测；1 小时 precise 未实测。
- 5 分钟 precise 的 Qwen diarization 会过切说话人；长音频显式 `--speakers 2` 或合并。
- AED 选型不是永久的；`ear/aed_registry.py` 的 `LAST_REVIEWED` 超过 6 个月要重查。
- Windows 原生支持 basic/precise；`privacy` 的 MOSS 仍未实现。

## 开发

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -e ".[dev,local]"
.venv/bin/python -m pytest -q
.venv/bin/python -m ear.cli --help
```

模型缓存：`~/.cache/ear/models`（`EAR_MODEL_DIR` 可覆盖）。下载支持 `HTTPS_PROXY` / `EAR_DOWNLOAD_PROXY`。

## 文档

- [Windows 原生支持](docs/windows.md)
- [DSH 音频/视频生态调研](docs/dsh-audio-ecosystem-2026-11-12.md)
- [输出 Schema](docs/output-schema.md)
- [按请求动态选策略](docs/request-strategies.md)
- [直接 ask vs 转录后 ask](docs/direct-vs-transcribe.md)
- [v2 架构](docs/architecture-v2.md)
- [水位结果](docs/eval-results-2026-11-11.md)
- [事件 refine](docs/refine-eval.md)
- [宣发整合版](https://github.com/HudsonHuang/agent-ear/blob/main/agent-ear-宣发整合版-2026-11.md)
- [AED 选型与敞口](docs/aed-selection.md)
- [Roadmap](docs/roadmap.md)
- [Schema 示例](schema/examples/)
- [Skill 源文件](skills/agent-ear/SKILL.md)
