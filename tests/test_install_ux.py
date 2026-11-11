"""Regression tests for the skill-install UX gaps found on a clean machine.

Background: `skills/agent-ear/scripts/agent-ear` is a thin wrapper around the
`agent-ear` CLI. Installing only the skill directory (``npx skills add`` or a
manual clone) gives you a skill that fails with ``exec: agent-ear: not found``,
and ``doctor`` used to report that install as ``OK``.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ear import install, setup

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "agent-ear"
WRAPPER = SKILL_ROOT / "scripts" / "agent-ear"
BASH = shutil.which("bash") or "bash"


# --- skill_health ---------------------------------------------------------


@pytest.mark.parametrize(
    "installed,wrapper_ok,cli_present,expected",
    [
        (False, False, False, "missing"),
        (False, True, True, "missing"),
        (True, False, True, "broken"),
        (True, True, False, "no-cli"),
        (True, True, True, "ok"),
    ],
)
def test_skill_health_matrix(installed, wrapper_ok, cli_present, expected):
    assert install.skill_health(
        installed=installed, wrapper_ok=wrapper_ok, cli_present=cli_present
    ) == expected


def test_every_health_state_has_a_label():
    for state in ("ok", "missing", "broken", "no-cli"):
        assert install.HEALTH_LABEL[state]


def test_list_skills_reports_no_cli_when_cli_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    install.install_skill(install.target("codex"))
    rows = install.list_skills(cli_present=False)
    codex = next(r for r in rows if r["target"] == "codex")
    assert codex["installed"] is True
    assert codex["wrapper_ok"] is True
    assert codex["health"] == "no-cli"


def test_list_skills_reports_ok_when_cli_present(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    install.install_skill(install.target("codex"))
    rows = install.list_skills(cli_present=True)
    codex = next(r for r in rows if r["target"] == "codex")
    assert codex["health"] == "ok"


# --- wrapper --------------------------------------------------------------


def _run_wrapper(env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(WRAPPER), "doctor"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Unix wrapper; Windows uses .cmd/.ps1")
def test_wrapper_explains_missing_cli():
    proc = _run_wrapper({"PATH": "/usr/bin:/bin", "HOME": "/tmp"})
    assert proc.returncode == 127
    assert "agent-ear CLI not found" in proc.stderr
    assert "uv tool install agent-ear" in proc.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="Unix wrapper; Windows uses .cmd/.ps1")
def test_wrapper_honours_agent_ear_bin(tmp_path):
    fake = tmp_path / "fake-agent-ear"
    fake.write_text("#!/bin/sh\necho FAKE-CLI \"$@\"\nexit 0\n")
    fake.chmod(0o755)
    proc = _run_wrapper({"PATH": "/usr/bin:/bin", "HOME": "/tmp",
                         "AGENT_EAR_BIN": str(fake)})
    assert proc.returncode == 0
    assert "FAKE-CLI doctor" in proc.stdout


def test_install_skill_wrappers_keep_cli_guard(tmp_path, monkeypatch):
    """setup rewrites wrappers; the fallback hint must survive that rewrite."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    dest = Path(install.install_skill(install.target("codex"))["path"])
    for name in ("agent-ear", "agent-ear.cmd", "agent-ear.ps1"):
        text = (dest / "scripts" / name).read_text(encoding="utf-8")
        assert "CLI not found" in text, name
        assert "127" in text, name
        assert "AGENT_EAR_BIN" in text, name


@pytest.mark.skipif(sys.platform == "win32", reason="Unix wrapper; Windows uses .cmd/.ps1")
def test_generated_wrapper_explains_missing_binary(tmp_path):
    dest = tmp_path / "skill"
    install._write_wrappers(dest, "/nonexistent/agent-ear")
    proc = subprocess.run(
        [BASH, str(dest / "scripts" / "agent-ear"), "doctor"],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"}, timeout=30,
    )
    assert proc.returncode == 127
    assert "agent-ear CLI not found" in proc.stderr
    assert "uv tool install agent-ear" in proc.stderr


# --- setup --skip-key -----------------------------------------------------


def _args(**kw) -> argparse.Namespace:
    base = dict(api_key_stdin=False, non_interactive=True, skip_key=False,
                base_url=None, force=False)
    base.update(kw)
    return argparse.Namespace(**base)


def test_non_interactive_skip_key_is_allowed(monkeypatch):
    """--non-interactive --skip-key must not require a key (skill-only installs)."""
    monkeypatch.setattr(setup.config, "get_qwen", lambda: {})
    key, base = setup._read_key(_args(skip_key=True))
    assert key == ""
    assert base


def test_non_interactive_without_key_still_fails(monkeypatch):
    monkeypatch.setattr(setup.config, "get_qwen", lambda: {})
    with pytest.raises(SystemExit) as exc:
        setup._read_key(_args())
    assert "skip-key" in str(exc.value.code)


def test_non_interactive_reuses_existing_key(monkeypatch):
    monkeypatch.setattr(
        setup.config, "get_qwen",
        lambda: {"api_key": "sk-existing", "base_url": "https://example.test"},
    )
    key, base = setup._read_key(_args())
    assert key == "sk-existing"
    assert base == "https://example.test"
