"""Read-only health checks for agent-ear (no network by default)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from . import __version__, aed_registry, config, install, media


def _mod(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def collect(*, check_api: bool = False, scope: str = "user",
            project_root: Path | None = None) -> dict[str, Any]:
    q = config.get_qwen()
    out: dict[str, Any] = {
        "version": __version__,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "ffmpeg": {"path": media.FFMPEG,
                   "found": Path(media.FFMPEG).is_file() if Path(media.FFMPEG).is_absolute()
                            else bool(shutil.which(media.FFMPEG))},
        "ffprobe": {"path": media.FFPROBE,
                    "found": Path(media.FFPROBE).is_file() if Path(media.FFPROBE).is_absolute()
                             else bool(shutil.which(media.FFPROBE))},
        "config": {
            "path": str(config.config_path()),
            "exists": config.config_path().is_file(),
            "key_configured": bool(q.get("api_key")),
            "key": config.mask(q.get("api_key") or ""),
            "source": q.get("source"),
            "base_url": q.get("base_url"),
        },
        "local": {m: _mod(m) for m in
                  ("torch", "torchaudio", "librosa", "beat_this", "panns_inference", "silero_vad")},
        "models": {},
        "aed": aed_registry.summary(),
        "skills": install.list_skills(scope=scope, project_root=project_root),
    }
    try:
        from .models import ensure_model
        out["models"]["psed_beats"] = bool(ensure_model("psed_beats", check_only=True))
        out["models"]["beat_this_small0"] = bool(ensure_model("beat_this_small0", check_only=True))
    except Exception as exc:
        out["models"]["error"] = type(exc).__name__
    if check_api:
        out["api"] = config.check_qwen() if q.get("api_key") else {"ok": False, "error": "no key"}
    else:
        out["api"] = {"checked": False}
    return out


def human(d: dict[str, Any]) -> str:
    lines = [f"agent-ear {d['version']}  ({d['platform']}, Python {d['python']})"]
    lines.append(f"ffmpeg: {'OK' if d['ffmpeg']['found'] else 'MISSING'}  "
                 f"ffprobe: {'OK' if d['ffprobe']['found'] else 'MISSING'}")
    c = d["config"]
    lines.append(f"key: {c['key']} ({c['source']}); config: {c['path']}")
    lines.append(f"base: {c['base_url']}")
    local = d["local"]
    lines.append("local: " + ", ".join(f"{k}={'Y' if v else 'N'}" for k, v in local.items()))
    lines.append("models: " + ", ".join(f"{k}={'Y' if v else 'N'}"
                                        for k, v in d["models"].items() if k != "error"))
    lines.append(f"aed: {d['aed']['default']} (reviewed {d['aed']['last_reviewed']})")
    for s in d["skills"]:
        label = install.HEALTH_LABEL.get(s.get("health", "missing"), s.get("health", "?"))
        lines.append(f"skill {s['target']}: {label} {s['path']}")
    if "ok" in d["api"] or d["api"].get("checked"):
        lines.append(f"api: {'OK' if d['api'].get('ok') else 'FAIL'} "
                     f"{d['api'].get('status') or d['api'].get('error') or ''}".rstrip())
    return "\n".join(lines)
