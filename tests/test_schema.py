import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def _schema():
    return json.loads((ROOT / "schema/audio-score.schema.json").read_text(encoding="utf-8"))


def test_real_output_matches_schema():
    score = json.loads((ROOT / "tests/fixtures/min_score.json").read_text(encoding="utf-8"))
    jsonschema.validate(score, _schema())


def test_schema_rejects_missing_timeline():
    score = json.loads((ROOT / "tests/fixtures/min_score.json").read_text(encoding="utf-8"))
    score.pop("timeline")
    try:
        jsonschema.validate(score, _schema())
    except jsonschema.ValidationError:
        return
    raise AssertionError("schema accepted a score without timeline")


def test_golden_examples():
    schema = _schema()
    for p in sorted((ROOT / "schema/examples").glob("*.json")):
        jsonschema.validate(json.loads(p.read_text(encoding="utf-8")), schema)
