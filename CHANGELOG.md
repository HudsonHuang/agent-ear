# Changelog

## 0.2.9 — 2026-11-12

- Fix Windows checkouts: the bundled PANNs label CSV may be CRLF; normalize before size validation so no Google Storage download is triggered.

## 0.2.8 — 2026-11-12

- Domestic mirrors (`hf-mirror.com`, `gh-proxy.com`, Aliyun/Tsinghua/UStC) bypass `HTTPS_PROXY` by default; explicit `EAR_DOWNLOAD_PROXY` still wins.
- Installers add `NO_PROXY` for domestic hosts, so a VPN does not slow package/model downloads.

## 0.2.7 — 2026-11-12

- Prefetch independent precise models (BEATs + Beat This!) in parallel before ASR/AED/beat steps; basic still downloads none.

## 0.2.6 — 2026-11-12

- China-first install: domestic PyPI mirrors, USTC uv/Python mirrors, `hf-mirror.com` models, `gh-proxy.com` for BEATs.
- Windows installer now downloads local ffmpeg/ffprobe first (gyan → gh-proxy BtbN → winget), installs uv via pip mirror/USTC zip, and avoids `--python 3.12` downloads.
- `agent-ear setup --install-ffmpeg` auto-downloads a local Windows ffmpeg; `media`/`doctor` discover it without PATH edits.
- Skill wrappers fall back to `uvx --from agent-ear agent-ear` when the CLI is missing.
- Models are still on-demand: basic downloads none; `precise`/events download lazily; `--download-models` downloads in parallel.
- PANNs 447-class labels are bundled (no Google Storage); `HF_ENDPOINT`/`EAR_HF_ENDPOINT` overrides supported.

## 0.2.5 — 2026-11-12

- Add `agent-ear export --format srt|edl` for subtitles/SDH and CMX3600 EDL.
- Add `agent-ear highlights --top N --by Laughter,Applause` with JSON/Markdown/EDL output.
- Add `agent-ear mixcheck` (LUFS/true peak/LRA/clipping/bands) and `agent-ear compare` for DAW/audio-generation feedback loops.
- Add `docs/editing-exports.md`; update README/SKILL with editing commands.

## 0.2.4 — 2026-11-11

- 修复 `setup --api-key-stdin` 在 Windows PowerShell 5.1 下的 BOM 问题：管道传入的 Key 可能带 `U+FEFF`（以及零宽空格等复制残留），现在会先清理再校验/保存。
- 修复 `setup --api-key-stdin` 校验失败后仍调用 `input()` 的问题：stdin 已被 Key 占用时会抛 `EOFError`；现在直接返回 3，不交互。
- 修复 beat tracker 返回空 BPM 时覆盖 Omni BPM 的问题：保留已有估算值，避免 precise/music 的 BPM 从数值退化为 `null`。
- Windows + DSH 实际安装测试反馈（PR #1）：PowerShell BOM、失败不阻塞、BPM 回退；CI Windows 3.10/3.12 通过。

## 0.2.3 — 2026-11-11

- 修复 `agent-ear setup` 安装 skill 时重写 wrapper、却丢掉「CLI not found」提示的问题：0.2.2 只修了 clone/npx 直接使用的包内 wrapper，setup 生成的绝对路径版本仍会在 CLI 消失时裸失败。现在生成的 `.sh` / `.cmd` / `.ps1` 先试安装时的绝对路径，再回退 PATH，最终打印安装指引并以 127 退出。
- Windows CI 修复：Unix wrapper 测试在 Windows 跳过，并新增跨平台的生成 wrapper 守卫断言，覆盖 setup 重写后的三个脚本。

## 0.2.2 — 2026-11-11

- 修复「只装 skill、未装 CLI」时的报错体验：skill 包装脚本（`.sh` / `.cmd` / `.ps1`）先探测 CLI，缺失时打印安装指引并以 127 退出，不再抛裸 `exec: agent-ear: not found`。
- `setup --non-interactive --skip-key` 现在真正跳过 Key 配置，并提示之后可运行 `agent-ear setup` 补上。
- `doctor` / `skill list` 新增 skill 健康状态（`OK` / `-` / `BROKEN` / `NO-CLI`），不再把缺少 CLI 的 skill 误报为正常。
- README 与安装脚本统一为「先装 CLI，再装 skill」；新增 12 条 install UX 回归测试。

## 0.2.1 — 2026-11-11

- Document **Qwen Omni API as a hard dependency** for basic/ask/precise/music.
- Clarify that only `privacy` avoids Qwen; precise also needs Qwen ASR.


## 0.2.0 — 2026-11-11

- Rename public product/Skill to **agent-ear**.
- Add `agent-ear setup` with Qwen key onboarding, API check, and config at `~/.config/agent-ear/config.json` (Windows: `%APPDATA%\agent-ear\config.json`).
- Add installers for **Codex**, **DSH**, and **Claude Code**; Windows uses `.cmd` / `.ps1` wrappers.
- Add native Windows support (PowerShell installer, APPDATA config, Windows skill paths).
- Add `doctor`, `config`, `skill`, and `uninstall` lifecycle commands.
- Add strict `audio-score` schema plus golden examples (`schema/examples/`).
- Package schema, skill assets, and PretrainedSED vendor code into the wheel.
- Add cross-platform CI and wheel smoke tests.

## 0.1.0

- Initial Ear MVP: Qwen ASR + BEATs Strong + Beat This! + fusion; basic/precise modes.
