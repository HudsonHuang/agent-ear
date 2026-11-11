"""PretrainedSED BEATs Strong: frame-level AudioSet Strong AED (40 ms).

Runs the vendored PretrainedSED runner in a subprocess.  This is the default
event backend when the checkpoint is available; PANNs is the fallback.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .events_panns import ZH
from .models import ensure_model

_HERE = Path(__file__).resolve().parent
VENDOR = _HERE / "_vendor" / "pretrainedsed"
if not (VENDOR / "ear_runner.py").is_file():
    VENDOR = _HERE.parent / "third_party" / "pretrainedsed"
RUNNER = VENDOR / "ear_runner.py"


class AedError(RuntimeError):
    pass


def available() -> bool:
    if not RUNNER.is_file():
        return False
    try:
        return ensure_model("psed_beats", check_only=True) is not None
    except Exception:
        return False


def analyze(wav_path: Path, *, device: str = "cpu", timeout: float = 3600) -> dict[str, Any]:
    checkpoint = ensure_model("psed_beats")
    if checkpoint is None:
        raise AedError("BEATs_strong_1.pt is not available")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
        out = Path(fh.name)
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(VENDOR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        cmd = [
            sys.executable, str(RUNNER),
            "--audio", str(wav_path),
            "--out", str(out),
            "--checkpoint", str(checkpoint),
            "--device", device,
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        if p.returncode != 0 or not out.is_file():
            raise AedError(f"PretrainedSED runner failed: {p.stderr[-800:] or p.stdout[-800:]}")
        data = json.loads(out.read_text(encoding="utf-8"))
    finally:
        try:
            out.unlink()
        except OSError:
            pass
    for e in data.get("events") or []:
        e["label_zh"] = ZH.get(e.get("label", ""), e.get("label", ""))
    for t in data.get("top_labels") or []:
        t["label_zh"] = ZH.get(t.get("label", ""), t.get("label", ""))
    data["provider"] = "pretrainedsed-beats-strong"
    data["quality"] = "frame-40ms"
    return data
