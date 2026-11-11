from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_skill_frontmatter_and_sync():
    src = ROOT / "skills" / "agent-ear" / "SKILL.md"
    text = src.read_text(encoding="utf-8")
    assert text.startswith("---\nname: agent-ear\n")
    assert "description:" in text.split("---", 2)[1]
    synced = ROOT / "ear" / "_data" / "skill" / "SKILL.md"
    assert synced.read_text(encoding="utf-8") == text
    for name in ("agent-ear", "agent-ear.cmd", "agent-ear.ps1"):
        assert (src.parent / "scripts" / name).is_file()


def test_packaged_schema_matches_root():
    import json
    root = json.loads((ROOT / "schema" / "audio-score.schema.json").read_text())
    pkg = json.loads((ROOT / "ear" / "_data" / "schema" / "audio-score.schema.json").read_text())
    assert root == pkg
