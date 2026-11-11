from ear import fuse


def _speech():
    return [{"id": "sp_0001", "start_ms": 0, "end_ms": 5000,
             "speaker": "S0", "text": "你好", "words": []}]


def _event():
    return [{"id": "ev_0001", "start_ms": 2000, "end_ms": 3000,
             "label": "Laughter", "label_zh": "笑声", "conf": 0.8,
             "salience": 0.9}]


def test_speech_event_overlap_is_speech_with_events():
    tl = fuse.merge_timeline(duration_ms=6000, speech=_speech(),
                             events=_event(), music=None)
    assert tl
    hit = [e for e in tl if e["kind"] == "speech" and e.get("events")]
    assert hit, tl
    assert "同时" in hit[0]["text"]
    assert "笑声" in hit[0]["text"]


def test_event_only_interval():
    tl = fuse.merge_timeline(duration_ms=6000, speech=[], events=_event(),
                             music=None)
    assert any(e["kind"] == "event" for e in tl)
    assert any("笑声" in e["text"] for e in tl)


def test_relations_after_and_over():
    speech = _speech()
    event = [{"id": "ev_0001", "start_ms": 5200, "end_ms": 6000,
              "label": "Laughter", "label_zh": "笑声", "conf": 0.8, "salience": 0.9}]
    music = {"id": "mu_0001", "bpm": 120, "beats_ms": [0, 500],
             "downbeats_ms": [0, 2000]}
    rels = fuse.build_relations(speech=speech, events=event, music=music)
    assert any(r["type"] == "over" for r in rels)
    after = [r for r in rels if r["type"] == "after"]
    assert after and after[0]["gap_ms"] == 200


def test_views_one_line_and_chapters():
    speech = _speech()
    views = fuse.build_views(duration_ms=6000, speech=speech, events=_event(),
                             music=None, timeline=[], speakers=["S0"])
    assert "1 段语音" in views["one_line"]
    assert "1 位说话人" in views["one_line"]
    assert views["chapters"]
