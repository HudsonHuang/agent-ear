from ear import aed_registry


def test_registry_default_and_aliases():
    assert aed_registry.default_id() == "psed_beats"
    assert aed_registry.resolve("auto") == "psed_beats"
    assert aed_registry.resolve("beats") == "psed_beats"
    assert aed_registry.resolve("panns") == "panns"
    s = aed_registry.summary()
    assert s["last_reviewed"]
    assert any(p["id"] == "psed_beats" for p in s["providers"])
