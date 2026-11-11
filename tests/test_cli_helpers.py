from ear import cli, media
from ear.asr_qwen import normalize


def test_turns_merge_same_speaker():
    segs = [
        {"speaker": "S0", "start_ms": 0, "end_ms": 1000, "text": "a"},
        {"speaker": "S0", "start_ms": 1100, "end_ms": 2000, "text": "b"},
        {"speaker": "S1", "start_ms": 3000, "end_ms": 4000, "text": "c"},
    ]
    turns = cli._turns(segs)
    assert len(turns) == 2
    assert turns[0]["end_ms"] == 2000
    assert turns[0]["text"] == "a b"


def test_turns_split_on_long_gap():
    segs = [
        {"speaker": "S0", "start_ms": 0, "end_ms": 1000, "text": "a"},
        {"speaker": "S0", "start_ms": 2000, "end_ms": 3000, "text": "b"},
    ]
    assert len(cli._turns(segs)) == 2


def test_fmt_ts():
    assert media.fmt_ts(0) == "00:00.00"
    assert media.fmt_ts(61_230) == "01:01.23"
    assert media.fmt_ts(3_600_000, always_hours=True) == "01:00:00.00"


def test_normalize_qwen():
    result = {
        "transcripts": [{
            "content_duration_in_milliseconds": 3000,
            "sentences": [{
                "begin_time": 100, "end_time": 2000, "text": "你好",
                "speaker_id": 1,
                "words": [
                    {"begin_time": 100, "end_time": 500, "text": "你",
                     "punctuation": "", "confidence": 0.9},
                    {"begin_time": 500, "end_time": 900, "text": "好",
                     "punctuation": "。", "confidence": 0.8},
                ],
            }],
        }],
        "usage": {"total_Tokens": 10},
    }
    out = normalize(result, language="zh")
    assert out["speech_ms"] == 3000
    assert out["segments"][0]["speaker"] == "S1"
    assert out["segments"][0]["id"] == "sp_0001"
    assert out["segments"][0]["words"][0]["t_ms"] == 100
    assert out["segments"][0]["words"][0]["d_ms"] == 400
