from ear import routing


def test_parse_and_plan():
    assert routing.parse_needs(None, mode="precise") == ["transcript", "events", "beat"]
    assert routing.parse_needs("none", mode="precise") == []
    assert routing.parse_needs("beat", mode="precise") == ["beat"]
    omni = {"segments": [{"text": "hi"}],
            "events": [{"label": "Laughter"}],
            "music": {"present": True}}
    p = routing.plan("precise", ["transcript", "events", "beat"], omni)
    assert p == {"omni": True, "asr": True, "aed": True, "beat": True}
    p = routing.plan("precise", ["beat"], omni)
    assert p == {"omni": True, "asr": False, "aed": False, "beat": True}
    p = routing.plan("basic", ["transcript"], omni)
    assert p == {"omni": True, "asr": False, "aed": False, "beat": False}
