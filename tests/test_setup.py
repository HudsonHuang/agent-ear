import io
import json
from argparse import Namespace

from ear import setup


def _args(**overrides):
    values = dict(
        target="codex", scope="user", project_root=None, api_key_stdin=True,
        base_url=None, skip_key=False, skip_api_check=True, non_interactive=True,
        with_local=False, download_models=False, force=True, dry_run=False,
    )
    values.update(overrides)
    return Namespace(**values)


def _isolate_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_EAR_CONFIG", str(tmp_path / "config.json"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    monkeypatch.setattr(setup.shutil, "which", lambda name: "ffmpeg")
    monkeypatch.setattr(setup, "_smoke", lambda: {"ok": True})
    monkeypatch.setattr(setup.doctor, "collect", lambda **kwargs: {})
    monkeypatch.setattr(setup.doctor, "human", lambda data: "")


def test_noninteractive_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_EAR_CONFIG", str(tmp_path / "config.json"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    monkeypatch.setattr("sys.stdin", io.StringIO("sk-test\n"))
    args = Namespace(
        target="codex", scope="user", project_root=None, api_key_stdin=True,
        base_url=None, skip_key=False, skip_api_check=True, non_interactive=True,
        with_local=False, download_models=False, force=True, dry_run=False,
    )
    rc = setup.run(args)
    assert rc == 0
    assert (tmp_path / "config.json").is_file()
    assert (tmp_path / "codex" / "skills" / "agent-ear" / "SKILL.md").is_file()


def test_stdin_key_strips_powershell_bom_and_zero_width(tmp_path, monkeypatch):
    _isolate_setup(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("\ufeffsk-test\u200b\n"))

    assert setup.run(_args()) == 0

    data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert data["qwen"]["api_key"] == "sk-test"


def test_stdin_key_failure_does_not_prompt(tmp_path, monkeypatch):
    _isolate_setup(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("sk-bad\n"))
    monkeypatch.setattr(
        setup.config, "check_qwen",
        lambda *args, **kwargs: {"ok": False, "status": 401},
    )

    def fail_if_prompted(*args, **kwargs):
        raise AssertionError("stdin is exhausted; setup must not prompt")

    monkeypatch.setattr("builtins.input", fail_if_prompted)

    rc = setup.run(_args(
        skip_api_check=False, non_interactive=False, force=False,
    ))

    assert rc == 3
    assert not (tmp_path / "config.json").exists()
