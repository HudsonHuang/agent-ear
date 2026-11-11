"""AED provider registry / extension point.

The default is a snapshot, not a permanent choice. At install time an agent
should re-check the registry and the upstream model landscape; adding a new
provider only requires an adapter that returns the same event schema.
"""
from __future__ import annotations

from typing import Any

LAST_REVIEWED = "2026-11-11"

PROVIDERS: dict[str, dict[str, Any]] = {
    "psed_beats": {
        "name": "PretrainedSED BEATs Strong",
        "frame_ms": 40,
        "classes": 447,
        "license": "MIT",
        "size_mb": 364,
        "default": True,
        "status": "default",
        "upstream": "https://github.com/fschmid56/PretrainedSED",
        "adapter": "ear.aed_psed:analyze",
        "notes": "40ms frame-level AudioSet Strong; strong general default",
    },
    "panns": {
        "name": "PANNs CNN14 (clip-window fallback)",
        "frame_ms": 5000,
        "classes": 527,
        "license": "MIT",
        "size_mb": 312,
        "default": False,
        "status": "fallback",
        "upstream": "https://github.com/qiuqiangkong/audioset_tagging_cnn",
        "adapter": "ear.events_panns:analyze",
        "notes": "clip-level fallback; not frame-level",
    },
}


def list_providers() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in PROVIDERS.items()]


def default_id() -> str:
    for k, v in PROVIDERS.items():
        if v.get("default"):
            return k
    return next(iter(PROVIDERS))


def resolve(name: str | None) -> str:
    if not name or name == "auto":
        return default_id()
    aliases = {"beats": "psed_beats", "psed": "psed_beats", "panns": "panns"}
    key = aliases.get(name, name)
    if key not in PROVIDERS:
        raise ValueError(f"unknown AED provider: {name}; available: {list(PROVIDERS)}")
    return key


def summary() -> dict[str, Any]:
    return {"last_reviewed": LAST_REVIEWED, "default": default_id(),
            "providers": list_providers()}
