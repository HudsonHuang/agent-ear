from ear import editing

SCORE = {
    "source": {"duration_ms": 10000, "fps": 25},
    "speech": {"segments": [
        {"start_ms": 1000, "end_ms": 2000, "speaker": "S1", "text": "hello"},
        {"start_ms": 3000, "end_ms": 4000, "speaker": "S1", "text": ""},
    ]},
    "events": [
        {"id": "ev1", "start_ms": 1500, "end_ms": 2500, "label": "Laughter",
         "label_zh": "笑声", "conf": 0.9, "salience": 0.9},
        {"id": "ev2", "start_ms": 6000, "end_ms": 7000, "label": "Applause",
         "label_zh": "掌声", "conf": 0.8, "salience": 0.8},
    ],
}


def test_srt():
    out = editing.srt(SCORE, sdh=True, speaker=True)
    assert "00:00:01,000 --> 00:00:02,000" in out
    assert "S1: hello" in out
    assert "[笑声]" in out
    assert "00:00:06,000 --> 00:00:07,000" in out


def test_edl():
    out = editing.edl(SCORE, fps=25)
    assert "TITLE: agent-ear" in out
    assert "00:00:01:13 00:00:02:12" in out
    assert "* FROM CLIP NAME: 笑声" in out


def test_highlights():
    items = editing.highlights(SCORE, top=2, pad_before=0, pad_after=0)
    assert len(items) == 2
    assert items[0]["label"] == "笑声"
    assert items[0]["start_ms"] == 1500
    md = editing.highlights_md(SCORE, items)
    assert "agent-ear highlights" in md
