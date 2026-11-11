# Changelog

## 0.2.3 — 2026-11-11

- 修复 `agent-ear setup` 安装 skill 时重写 wrapper、却丢掉「CLI not found」提示的问题：生成的 `.sh` / `.cmd` / `.ps1` 现在先试安装时的绝对路径，再回退 PATH，最终打印安装指引并以 127 退出。
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
