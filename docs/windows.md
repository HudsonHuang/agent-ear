# Windows 原生支持（中国网络优先）

agent-ear 的 CLI 是纯 Python，依赖 ffmpeg 和可选 PyTorch；**Windows 10/11 原生 PowerShell 可用**，不要求 WSL。

> **强依赖：Qwen Omni API。** basic/ask/precise/music 都需要 `qwen3.8-omni-flash` 的 API Key 和网络；Windows 也一样。`privacy` 是唯一不调用 Qwen 的模式。

## 1. 推荐：一键安装

```powershell
irm https://raw.githubusercontent.com/HudsonHuang/agent-ear/main/install.ps1 | iex
```

不需要预装 Python/uv/ffmpeg。安装器会按顺序尝试：

| 依赖 | 首选 | 兜底 |
|---|---|---|
| ffmpeg/ffprobe | gyan.dev 静态 zip | `gh-proxy.com` 的 BtbN 包 → winget |
| uv | 已有 uv → 国内 pip 镜像装 uv | USTC 的 uv 二进制 → 官方脚本 |
| agent-ear | 阿里云 PyPI | 清华 PyPI → pypi.org |
| ffmpeg 位置 | `%LOCALAPPDATA%\agent-ear\ffmpeg\bin` | 系统 PATH |

下载默认用 `curl.exe --noproxy "*"`，**即使开了 VPN 也优先走国内源**；失败后才允许系统代理。

## 2. 手动安装

```powershell
# 如果已有 uv
uv tool install agent-ear
agent-ear setup --install-ffmpeg
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

## 3. 模型：不预装，按需并行下载

基础模式**不下载任何模型**，只调 Qwen Omni。  
第一次用 `precise` / 事件 / beat 时才下载：

```text
precise: BEATs Strong (~364MB) + Beat This! small0 (~8MB) + PANNs (~327MB)
```

- 默认 `HF_ENDPOINT=https://hf-mirror.com`；可覆盖。
- BEATs 先走 `gh-proxy.com`，失败直连 GitHub。
- PANNs 447 类标签已内置，不访问 Google Storage。
- 预下载（并行）：`agent-ear setup --download-models`。

## 4. 在 Codex / DSH / Claude 里用

Skill 内部调用：

```text
scripts\agent-ear.cmd ...
```

如果 CLI 不在 PATH，wrapper 会尝试 `uvx --from agent-ear agent-ear ...`（首次会下载/缓存），再不行才报错。

## 5. 常用命令

```powershell
agent-ear doctor --json
agent-ear ask input.mp4 "这段音频里发生了什么？"
agent-ear listen input.mp4 --mode basic --out .ear\my-video
agent-ear listen input.mp4 --mode precise --need transcript,events,beat --out .ear\my-video-precise
agent-ear export .ear\my-video --format srt
agent-ear mixcheck render.wav --json
```

## 6. 已知限制

- `privacy` 的 MOSS 后端仍未实现；basic 需要联网。
- `precise` 依赖的 PyTorch/Beat This! 轮子以官方 Windows wheel 为准；装不上时 basic 仍可用。
- 控制台中文乱码时先 `chcp 65001`；PowerShell 7 更好。
- 长路径/OneDrive 同步目录可能触发 ffmpeg 路径问题；建议把素材放在短路径。
- 卸载 Skill 用 `agent-ear uninstall`；配置在 `%APPDATA%\agent-ear`，`--purge` 才删。
