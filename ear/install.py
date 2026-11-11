"""Install/uninstall agent-ear Skill files for Codex, DSH, and Claude Code."""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import __version__

SKILL_NAME = "agent-ear"
MARKER = ".agent-ear-installed.json"
TARGETS = ("codex", "dsh", "claude")


class InstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    name: str
    root: Path
    label: str


def _home(name: str, default: str) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else Path.home() / default


def target(name: str) -> Target:
    n = name.lower()
    if n in ("codex", "codex-cli"):
        return Target("codex", _home("CODEX_HOME", ".codex"), "Codex")
    if n in ("dsh", "deepseek-harness"):
        return Target("dsh", _home("DSH_HOME", ".dsh"), "DeepSeek Harness")
    if n in ("claude", "claude-code"):
        root = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")).expanduser()
        return Target("claude", root, "Claude Code")
    raise InstallError(f"unknown target: {name}; choose {', '.join(TARGETS)}")


def parse_targets(raw: str | None) -> list[Target]:
    if not raw or raw == "auto":
        return [target("codex")]
    raw = raw.replace(" ", ",")
    names = ["codex", "dsh", "claude"] if raw == "all" else [x for x in raw.split(",") if x]
    out: list[Target] = []
    for n in names:
        t = target(n)
        if t.name not in {x.name for x in out}:
            out.append(t)
    return out


def skill_source() -> Path:
    here = Path(__file__).resolve().parent
    p = here / "_data" / "skill"
    if (p / "SKILL.md").is_file():
        return p
    # repo/dev fallback
    p = here.parent / "skills" / SKILL_NAME
    if (p / "SKILL.md").is_file():
        return p
    raise InstallError("skill assets missing from package (ear/_data/skill)")


def skill_dest(t: Target, scope: str = "user", project_root: Path | None = None) -> Path:
    if scope == "project":
        root = (project_root or Path.cwd()).resolve()
        sub = {"codex": ".codex", "dsh": ".dsh", "claude": ".claude"}[t.name]
        return root / sub / "skills" / SKILL_NAME
    return t.root / "skills" / SKILL_NAME


def _binary() -> str:
    argv0 = Path(sys.argv[0]).expanduser()
    if argv0.name.lower() in ("agent-ear", "agent-ear.exe") and argv0.is_file():
        return str(argv0.resolve())
    return shutil.which("agent-ear") or shutil.which("ear") or "agent-ear"


def _is_path_like(binary: str) -> bool:
    return Path(binary).is_absolute() or "/" in binary or "\\" in binary


def _write_wrappers(dest: Path, binary: str) -> None:
    """Write platform wrappers that prefer the setup-time CLI path.

    The absolute path keeps the skill working when the CLI is installed but not
    yet on PATH. If that binary disappears (e.g. ``uv tool uninstall``), the
    wrapper must fall back to PATH and otherwise explain what is missing instead
    of failing with a raw ``No such file or directory`` (exit 127).
    """
    scripts = dest / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    path_like = _is_path_like(binary)
    # Unix
    unix = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'if [[ -n "${AGENT_EAR_BIN:-}" ]]; then',
        '  exec "$AGENT_EAR_BIN" "$@"',
        "fi",
    ]
    if path_like:
        unix += [
            f'BIN="{binary}"',
            'if [ -x "$BIN" ]; then',
            '  exec "$BIN" "$@"',
            "fi",
        ]
    unix += [
        "if command -v agent-ear >/dev/null 2>&1; then",
        '  exec agent-ear "$@"',
        "fi",
        "cat >&2 <<'MSG'",
        "agent-ear CLI not found on PATH.",
        "This skill is a thin wrapper; install the CLI first:",
        "  uv tool install agent-ear      # recommended",
        "  pipx install agent-ear",
        "  python3 -m pip install --user agent-ear",
        "Then re-run this script (or set AGENT_EAR_BIN to the binary path).",
        "MSG",
        "exit 127",
    ]
    sh = scripts / "agent-ear"
    sh.write_text("\n".join(unix) + "\n", encoding="utf-8")
    try:
        sh.chmod(0o755)
    except OSError:
        pass
    # Windows cmd
    cmd = [
        "@echo off",
        "setlocal",
        'if not "%AGENT_EAR_BIN%"=="" goto use_env',
    ]
    if path_like:
        cmd += [f'if exist "{binary}" goto use_abs']
    cmd += [
        "where agent-ear >nul 2>nul",
        "if errorlevel 1 goto no_cli",
        "agent-ear %*",
        "exit /b %ERRORLEVEL%",
        ":use_env",
        '"%AGENT_EAR_BIN%" %*',
        "exit /b %ERRORLEVEL%",
    ]
    if path_like:
        cmd += [
            ":use_abs",
            f'"{binary}" %*',
            "exit /b %ERRORLEVEL%",
        ]
    cmd += [
        ":no_cli",
        "echo agent-ear CLI not found on PATH. 1>&2",
        "echo This skill is a thin wrapper; install the CLI first: 1>&2",
        "echo   uv tool install agent-ear 1>&2",
        "echo   pipx install agent-ear 1>&2",
        "echo   python -m pip install --user agent-ear 1>&2",
        "exit /b 127",
    ]
    (scripts / "agent-ear.cmd").write_text("\r\n".join(cmd) + "\r\n", encoding="utf-8")
    # PowerShell
    ps = [
        '$ErrorActionPreference = "Stop"',
        "if ($env:AGENT_EAR_BIN) {",
        "  & $env:AGENT_EAR_BIN @args",
        "  exit $LASTEXITCODE",
        "}",
    ]
    if path_like:
        ps += [
            f'$bin = "{binary}"',
            "if (Test-Path -LiteralPath $bin -PathType Leaf) {",
            "  & $bin @args",
            "  exit $LASTEXITCODE",
            "}",
        ]
    ps += [
        "if (-not (Get-Command agent-ear -ErrorAction SilentlyContinue)) {",
        "  @(",
        '    "agent-ear CLI not found on PATH.",',
        '    "This skill is a thin wrapper; install the CLI first:",',
        '    "  uv tool install agent-ear",',
        '    "  pipx install agent-ear",',
        '    "  python -m pip install --user agent-ear"',
        "  ) | ForEach-Object { [Console]::Error.WriteLine($_) }",
        "  exit 127",
        "}",
        "& agent-ear @args",
        "exit $LASTEXITCODE",
    ]
    (scripts / "agent-ear.ps1").write_text("\r\n".join(ps) + "\r\n", encoding="utf-8")


def install_skill(t: Target, *, scope: str = "user", project_root: Path | None = None,
                  force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    src = skill_source()
    dest = skill_dest(t, scope, project_root)
    exists = dest.exists()
    if dry_run:
        return {"target": t.name, "path": str(dest), "would_install": True,
                "exists": exists, "force": force}
    if exists:
        marker = dest / MARKER
        same = False
        if marker.is_file():
            try:
                m = json.loads(marker.read_text(encoding="utf-8"))
                same = m.get("version") == __version__ and m.get("name") == SKILL_NAME
            except Exception:
                pass
        if same and not force:
            return {"target": t.name, "path": str(dest), "installed": True, "unchanged": True}
        if not force:
            raise InstallError(
                f"{t.label} skill already exists at {dest}; re-run with --force to overwrite")
        backup = dest.with_name(f"{SKILL_NAME}.bak.{time.strftime('%Y%m%d-%H%M%S')}")
        dest.rename(backup)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    _write_wrappers(dest, _binary())
    marker = {"name": SKILL_NAME, "version": __version__, "target": t.name,
              "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "source": str(src)}
    (dest / MARKER).write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"target": t.name, "path": str(dest), "installed": True, "version": __version__}


def uninstall_skill(t: Target, *, scope: str = "user", project_root: Path | None = None,
                    force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    dest = skill_dest(t, scope, project_root)
    if not dest.exists():
        return {"target": t.name, "path": str(dest), "removed": False, "missing": True}
    marker = dest / MARKER
    if not marker.is_file() and not force:
        raise InstallError(f"{dest} does not look like an agent-ear install; use --force")
    if dry_run:
        return {"target": t.name, "path": str(dest), "would_remove": True}
    shutil.rmtree(dest)
    return {"target": t.name, "path": str(dest), "removed": True}


def skill_health(*, installed: bool, wrapper_ok: bool, cli_present: bool) -> str:
    """Classify an installed skill by whether it can actually run.

    A skill directory can be present while still being unusable: the shipped
    scripts/agent-ear is a thin wrapper that execs the ``agent-ear`` CLI, and
    skill-only installs (``npx skills add``, manual clone) do not install it.
    """
    if not installed:
        return "missing"
    if not wrapper_ok:
        return "broken"
    if not cli_present:
        return "no-cli"
    return "ok"


HEALTH_LABEL = {
    "ok": "OK",
    "missing": "-",
    "broken": "BROKEN (scripts/agent-ear 缺失或不可执行)",
    "no-cli": "NO-CLI (先装 CLI： uv tool install agent-ear)",
}


def list_skills(*, scope: str = "user", project_root: Path | None = None,
                cli_present: bool | None = None) -> list[dict[str, Any]]:
    if cli_present is None:
        cli_present = shutil.which("agent-ear") is not None
    out = []
    for name in TARGETS:
        t = target(name)
        dest = skill_dest(t, scope, project_root)
        installed = dest.is_dir()
        wrapper = dest / "scripts" / "agent-ear"
        wrapper_ok = wrapper.is_file() and os.access(wrapper, os.X_OK)
        row: dict[str, Any] = {
            "target": t.name,
            "path": str(dest),
            "installed": installed,
            "wrapper_ok": wrapper_ok,
            "cli_present": cli_present,
            "health": skill_health(installed=installed, wrapper_ok=wrapper_ok,
                                   cli_present=cli_present),
        }
        marker = dest / MARKER
        if marker.is_file():
            try:
                m = json.loads(marker.read_text(encoding="utf-8"))
                row.update({"version": m.get("version"), "installed_at": m.get("installed_at")})
            except Exception:
                pass
        out.append(row)
    return out
