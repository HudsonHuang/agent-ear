# 对外事实卡（2026-11-11）

> 宣发材料以本页为准；旧文里的 `ear` 名称、安装方式、DSH 机制、数字如与本页冲突，以本页为准。

## 名称与安装

- 产品 / Skill / PyPI：**agent-ear**
- CLI：`agent-ear`
- 安装：
  ```bash
  uv tool install agent-ear
  agent-ear setup
  ```
- Windows：`winget install Gyan.FFmpeg` + 上面两条；见 [Windows](windows.md)。
- 支持：Codex、DSH、Claude Code。
- 仓库：`github.com/HudsonHuang/agent-ear`（发布时确认 owner）。

## 能力边界

- **basic（默认）**：详细转录/描述，0.5–2s 时间戳，能粗剪；需要 Qwen API。
- **precise**：Qwen ASR 词级 + BEATs 40ms + Beat This!；需要 `agent-ear[local]`。
- **local-first, cloud optional**：basic 要联网；`privacy` 才不调用 API。
- 不做：Live Translation、实时流、空间声学、声纹、完整总谱。
- 40ms 只属于 precise；不要写成 basic 也 40ms。

## 实测数字

| 项 | 数值 |
|---|---:|
| 1 小时 basic | 231s，RTF 0.064，¥0.211/音频小时 |
| 5 分钟 precise | 57s，RTF 0.19 |
| 5 分钟只要笑声 basic / precise | 15.2s / 24.1s；53/65 refine |
| Omni QA（180 条） | 87.2% |
| 直接 ask vs 一次转录+回答 | 87.2% vs 80.0% |
| 转录后强文本（40 条子集） | 77.5% |

诚实结论：**价值在“可下刀的时间轴/证据”，不是“QA 超过 Omni”**。单问题最高准确率是直接 `ask`。

## DSH 机制（重要修正）

- DSH **Skill** 放 `<DSH_HOME>/skills/agent-ear`，由目录扫描发现。
- 不需要 `dsh plugin add`，不需要 `dsh.bundle.patch`；后者是 DSH **plugin** 的打包字段。
- 如果未来要进 DSH Discover 插件目录，再单独做 npm bundle。

## 安装后路径

- Codex：`$CODEX_HOME/skills/agent-ear` / `%USERPROFILE%\.codex\skills\agent-ear`
- DSH：`$DSH_HOME/skills/agent-ear` / `%USERPROFILE%\.dsh\skills\agent-ear`
- Claude：`~/.claude/skills/agent-ear`
