import json
from pathlib import Path

from ear import install


def test_codex_install_and_uninstall(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    t = install.target("codex")
    r = install.install_skill(t)
    dest = Path(r["path"])
    assert (dest / "SKILL.md").is_file()
    assert (dest / "scripts" / "agent-ear.cmd").is_file()
    marker = json.loads((dest / ".agent-ear-installed.json").read_text())
    assert marker["name"] == "agent-ear"
    # idempotent
    assert install.install_skill(t).get("unchanged") is True
    u = install.uninstall_skill(t)
    assert u["removed"] is True
    assert not dest.exists()


def test_project_scope(tmp_path):
    t = install.target("dsh")
    r = install.install_skill(t, scope="project", project_root=tmp_path / "repo")
    assert Path(r["path"]) == tmp_path / "repo" / ".dsh" / "skills" / "agent-ear"
