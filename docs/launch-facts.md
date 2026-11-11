# 对外事实卡（2026-11-11）

> 宣发材料以本页为准；旧文里的 `ear` 名称、安装方式、DSH 机制、数字如与本页冲突，以本页为准。

## 名称与安装

- 当前版本：**0.2.5**（PyPI / GitHub）；npm DSH bundle 最新 **0.2.4**（0.2.5 待 npm 2FA）
- 产品 / Skill / PyPI：**agent-ear**
- CLI：`agent-ear`
- 安装：
  ```bash
  uv tool install agent-ear
  agent-ear setup
  ```
- Windows：`winget install Gyan.FFmpeg` + 上面两条；见 [Windows](windows.md)。
- Windows + DSH 已实测；PR #1 修复 PowerShell BOM、stdin 失败提示、BPM 回退。
- 支持：Codex、DSH、Claude Code。
- 仓库：`github.com/HudsonHuang/agent-ear`（发布时确认 owner）。

## 强依赖（必须写）

- **basic / ask / precise / music 都依赖 Qwen Omni 模型 API**（默认 `qwen3.8-omni-flash`）。
- 没有 Omni Key/网络时，只有 `privacy` 本地降级可用；不要宣传成“完全离线/本地优先”。
- precise 还额外依赖 Qwen ASR；本地 BEATs/Beat This! 只是精修层，不是 Omni 的替代。

## 能力边界

- **basic（默认）**：详细转录/描述，0.5–2s 时间戳，能粗剪；需要 Qwen API。
- **precise**：Qwen ASR 词级 + BEATs 40ms + Beat This!；需要 `agent-ear[local]`。
- **不是 local-first/cloud optional**：basic/ask/precise/music 都依赖 Qwen Omni；只有 `privacy` 不调用 API。
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
