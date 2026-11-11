import json
from pathlib import Path

import jsonschema
from ear import score


def test_from_omni_and_refine():
    omni = {
        "provider": "qwen3.8-omni-flash",
        "summary": "two people laugh",
        "segments": [
            {"start_ms": 0, "end_ms": 900, "speaker": "S1", "text": "hi"},
            {"start_ms": 900, "end_ms": 1800, "speaker": "S2", "text": "hello"},
        ],
        "events": [{"start_ms": 6000, "end_ms": 8000, "label": "laughter"}],
        "music": {"present": False, "description": "", "bpm": None},
        "usage": {}, "wall_s": 0.1, "chunks": 1,
    }
    s = score.from_omni(omni, source_path="x.wav", sha256="x", duration_ms=10000)
    assert s["capabilities"]["omni"] == "qwen3.8-omni-flash"
    assert s["events"][0]["label"] == "Laughter"
    assert s["events"][0]["precision"] == "omni-coarse"
    n = score.refine_events(s, [{"start_ms": 6100, "end_ms": 7900,
                                 "label": "Laughter", "conf": 0.9, "salience": 0.9}])
    assert n == 1
    assert s["events"][0]["precision"] == "refined-40ms"
    assert s["events"][0]["start_ms"] == 6100
    schema = json.loads(Path("schema/audio-score.schema.json").read_text())
    jsonschema.validate(s, schema)


def test_refine_keeps_omni_when_no_match():
    omni = {"provider": "m", "segments": [], "summary": "",
            "events": [{"start_ms": 1000, "end_ms": 2000, "label": "bird chirping"}],
            "music": {"present": False}}
    s = score.from_omni(omni, source_path="x", sha256="x", duration_ms=3000)
    assert score.refine_events(s, [{"start_ms": 1000, "end_ms": 2000,
                                    "label": "Laughter", "conf": 0.9}]) == 0
    assert s["events"][0]["precision"] == "omni-coarse"


def test_apply_beats_keeps_omni_bpm_when_tracker_has_none():
    omni = {"provider": "m", "segments": [], "summary": "",
            "events": [],
            "music": {"present": True, "description": "chiptune", "bpm": 150}}
    s = score.from_omni(omni, source_path="x", sha256="x", duration_ms=20000)

    score.apply_beats(s, {
        "bpm": None, "beats_ms": [100, 500], "downbeats_ms": [],
        "beat_positions": [1, 2], "quality": "fallback", "provider": "librosa",
    }, 20000)

    track = s["music"]["tracks"][0]
    assert track["bpm"] == 150
    assert track["beats_ms"] == [100, 500]
    assert track["quality"] == "fallback"

    score.apply_beats(s, {
        "bpm": 272.7, "beats_ms": [100, 320], "downbeats_ms": [100],
        "beat_positions": [1, 2], "quality": "model", "provider": "beat_this-small0",
    }, 20000)

    assert track["bpm"] == 272.7
