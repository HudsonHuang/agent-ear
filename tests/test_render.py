import json
from pathlib import Path

from ear import render

ROOT = Path(__file__).resolve().parents[1]


def _score():
    return json.loads((ROOT / "tests/fixtures/min_score.json").read_text(encoding="utf-8"))


def test_hearing_has_required_sections():
    md = render.render_hearing(_score())
    for heading in ("## 概览", "## 章节", "## 事件索引", "## 限制"):
        assert heading in md
    assert "00:00" in md


def test_digest_levels():
    s = _score()
    l0 = render.render_digest(s, level=0)
    l1 = render.render_digest(s, level=1)
    assert "## 章节" not in l0
    assert "## 章节" in l1
