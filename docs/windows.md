# Windows 原生支持

agent-ear 的 CLI 是纯 Python，依赖 ffmpeg 和可选 PyTorch；**Windows 10/11 原生 PowerShell 可用**，不要求 WSL。Windows 与 macOS/Linux 的差异主要是路径、wrapper 和 ffmpeg 安装。

> **强依赖：Qwen Omni API。** basic/ask/precise/music 都需要 `qwen3.8-omni-flash` 的 API Key 和网络；Windows 也一样。`privacy` 是唯一不调用 Qwen 的模式。

## 1. 前置

```powershell
winget install Gyan.FFmpeg
winget install astral-sh.uv
```

- Python 3.10–3.12（`uv` 会自动管理）。
- `ffmpeg`、`ffprobe` 必须在 PATH。
- 只装 basic 不需要 PyTorch；precise 的 `[local]` 会装 torch/torchaudio/librosa 等，体积较大。

## 2. 安装

```powershell
uv tool install agent-ear
agent-ear setup
```

`setup` 会问 Qwen API Key、安装目标（Codex/DSH/Claude），写入：

```text
%APPDATA%\agent-ear\config.json
```

并安装 Skill：

```text
%USERPROFILE%\.codex\skills\agent-ear
%USERPROFILE%\.dsh\skills\agent-ear
%USERPROFILE%\.claude\skills\agent-ear
```

如果 `agent-ear` 还不在当前 PowerShell 的 PATH，重开终端，或用：

```powershell
& "$env:USERPROFILE\.local\bin\agent-ear.exe" setup
```

## 3. 在 Codex / DSH / Claude 里用

Skill 内部调用：

```text
scripts\agent-ear.cmd ...
```

Codex 重启后 `/skills` 查看；DSH 新会话；Claude 输入 `/agent-ear`。

## 4. 常用命令

```powershell
agent-ear doctor --json
agent-ear ask input.mp4 "这段音频里发生了什么？"
agent-ear listen input.mp4 --mode basic --out .ear\my-video
agent-ear listen input.mp4 --mode precise --need transcript,events,beat --out .ear\my-video-precise
agent-ear config show
agent-ear uninstall --target codex
```

## 5. 已知 Windows 限制

- `privacy` 的 MOSS 后端仍未实现；basic 需要联网。
- `precise` 依赖的 PyTorch/Beat This! 轮子以官方 Windows wheel 为准；装不上时 basic 仍可用。
- 控制台中文乱码时先 `chcp 65001`；PowerShell 7 更好。
- 长路径/OneDrive 同步目录可能触发 ffmpeg 路径问题；建议把素材放在短路径。
- 卸载 Skill 用 `agent-ear uninstall`；配置在 `%APPDATA%\agent-ear`，`--purge` 才删。
