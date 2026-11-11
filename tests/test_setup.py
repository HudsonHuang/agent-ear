import io
from argparse import Namespace

from ear import setup


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
