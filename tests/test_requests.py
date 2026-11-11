from ear.requests import parse_request


def test_laughter_extract():
    p = parse_request("把视频里所有笑声都剪出来")
    assert p.intent == "events"
    assert "Laughter" in p.labels
    assert p.needs == ["events"]


def test_beat_and_default():
    assert parse_request("按节拍卡点").intent == "beat"
    assert parse_request(None) is None
    assert parse_request("详细记录一下").intent == "transcribe"
