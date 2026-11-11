"""Interactive first-run setup for agent-ear."""
from __future__ import annotations

import getpass
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import config, doctor, install


def _say(msg: str = "") -> None:
    print(msg, flush=True)


def _read_key(args) -> tuple[str, str]:
    q = config.get_qwen()
    existing = q.get("api_key") or ""
    if args.api_key_stdin:
        key = sys.stdin.readline().strip()
        if not key:
            raise SystemExit("no key on stdin")
        return key, (args.base_url or q.get("base_url") or config.DEFAULT_BASE)
    if args.non_interactive:
        if existing and not args.skip_key:
            return existing, (args.base_url or q.get("base_url") or config.DEFAULT_BASE)
        raise SystemExit("--non-interactive needs an existing key or --api-key-stdin")
    if existing:
        _say(f"当前 Key：{config.mask(existing)}（来源 {q.get('source')}）")
        _say("回车保留，或粘贴新 Key（输入不回显）。")
    else:
        _say("需要阿里云百炼 / DashScope 的 Qwen API Key。")
        _say("获取：https://bailian.console.aliyun.com/  → API-KEY")
    key = getpass.getpass("Qwen API Key: ").strip()
    key = key or existing
    if not key:
        raise SystemExit("未提供 Key；可稍后运行 `agent-ear setup`")
    base = args.base_url or q.get("base_url") or config.DEFAULT_BASE
    if not args.base_url and not args.non_interactive:
        raw = input(f"Base URL [{base}]: ").strip()
        base = raw or base
    return key, base


def _choose_targets(args) -> list[install.Target]:
    if args.target:
        return install.parse_targets(args.target)
    if args.non_interactive:
        return [install.target("codex")]
    # Detect likely agents; Codex is always offered.
    names = ["codex"]
    if (Path.home() / ".dsh").exists() or os.environ.get("DSH_HOME"):
        names.append("dsh")
    if (Path.home() / ".claude").exists() or os.environ.get("CLAUDE_CONFIG_DIR"):
        names.append("claude")
    _say("安装目标：")
    for i, n in enumerate(names, 1):
        _say(f"  {i}. {install.target(n).label}")
    raw = input("选择（逗号分隔，回车=全部）: ").strip()
    if not raw:
        return [install.target(n) for n in names]
    picked = []
    for part in raw.replace(" ", ",").split(","):
        if part.isdigit() and 1 <= int(part) <= len(names):
            picked.append(install.target(names[int(part) - 1]))
        elif part:
            picked.append(install.target(part))
    return picked or [install.target("codex")]


def _smoke() -> dict[str, Any]:
    from . import media
    if not media.FFMPEG:
        return {"ok": False, "error": "ffmpeg missing"}
    with tempfile.TemporaryDirectory(prefix="agent-ear-smoke-") as td:
        wav = Path(td) / "smoke.wav"
        p = media.run([media.FFMPEG, "-y", "-v", "error", "-f", "lavfi",
                       "-i", "sine=frequency=440:duration=1", "-ar", "16000",
                       "-ac", "1", str(wav)], timeout=30)
        if p.returncode != 0 or not wav.is_file():
            return {"ok": False, "error": "ffmpeg smoke failed"}
        info = media.media_info(wav)
        return {"ok": bool(info.get("has_audio")), "duration_ms": info.get("duration_ms")}


def run(args) -> int:
    _say(f"agent-ear setup  v{__import__('ear').__version__}")
    _say("basic 模式会把音频上传到阿里云 Qwen 做理解；privacy 模式不调用 API。")
    _say("")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        hint = ("winget install Gyan.FFmpeg" if sys.platform.startswith("win")
                else "brew install ffmpeg" if sys.platform == "darwin"
                else "sudo apt install ffmpeg")
        _say(f"缺少 ffmpeg/ffprobe。请先安装：{hint}")
        return 2

    key, base = _read_key(args)
    if not key:
        return 2
    if not args.skip_api_check:
        _say("检查 Key ...")
        check = config.check_qwen(key, base)
        if not check.get("ok"):
            _say(f"Key 检查失败（{check.get('status') or check.get('error')}）。"
                 "请确认 Key、base URL 与模型权限。")
            if not args.non_interactive:
                if input("仍然保存并继续？[y/N] ").strip().lower() != "y":
                    return 3
            elif not args.force:
                return 3
    if args.dry_run:
        _say(f"[dry-run] would write config {config.config_path()}")
    else:
        path = config.save_qwen(key, base)
        _say(f"配置已写入 {path}（权限 0600）")

    targets = _choose_targets(args)
    for t in targets:
        try:
            r = install.install_skill(t, scope=args.scope, project_root=args.project_root,
                                      force=args.force, dry_run=args.dry_run)
            _say(f"  {t.label}: {'OK' if r.get('installed') else 'DRY-RUN'} {r.get('path')}")
        except install.InstallError as exc:
            _say(f"  {t.label}: {exc}")
            return 4

    if args.with_local:
        missing = [m for m in ("torch", "librosa", "beat_this", "panns_inference")
                   if __import__("importlib.util", fromlist=["util"]).find_spec(m) is None]
        if missing:
            _say(f"local 依赖未安装（{', '.join(missing)}）。")
            _say('请运行：uv tool install "agent-ear[local]" --force')
    if args.download_models:
        from .models import ensure_model
        for name in ("psed_beats", "beat_this_small0"):
            _say(f"下载模型 {name} ...")
            ensure_model(name)
        _say("模型下载完成")

    _say("")
    _say("smoke: " + json.dumps(_smoke(), ensure_ascii=False))
    d = doctor.collect(check_api=False, scope=args.scope, project_root=args.project_root)
    _say(doctor.human(d))
    _say("")
    for t in targets:
        if t.name == "codex":
            _say("Codex：重启后让它使用 agent-ear；或输入 /skills 查看。")
        elif t.name == "dsh":
            _say("DSH：新开一个会话，技能目录会出现 agent-ear。")
        elif t.name == "claude":
            _say("Claude Code：新会话输入 /agent-ear。")
    return 0
