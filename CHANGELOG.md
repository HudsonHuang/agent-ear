# Changelog

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
