import subprocess
from pathlib import Path

from ear import mix


def _sine(path: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=1", "-ar", "16000",
                    "-ac", "1", str(path)], check=True)


def test_mix_analyze_and_compare(tmp_path):
    a = tmp_path / "a.wav"
    _sine(a)
    d = mix.analyze(a)
    assert d["duration_s"] == 1.0
    assert d["lufs"] is not None
    assert d["bands_pct"]["mid"]["pct"] > 50
    c = mix.compare(a, a)
    assert c["delta_b_minus_a"]["lufs"] == 0
