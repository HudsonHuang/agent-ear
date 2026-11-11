"""agent-ear configuration and credential resolution.

Write path is platform-aware and private; read path also accepts the legacy
ear/bailian locations so existing users keep working.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

APP = "agent-ear"
DEFAULT_BASE = "https://dashscope.aliyuncs.com"
DEFAULT_OMNI = "qwen3.8-omni-flash"
DEFAULT_ASR = "qwen-audio-3.1-asr-flash-filetrans"


def _home() -> Path:
    return Path.home()


def config_path() -> Path:
    raw = os.environ.get("AGENT_EAR_CONFIG") or os.environ.get("LLMEAR_CONFIG")
    if raw:
        return Path(raw).expanduser()
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or (str(_home() / "AppData" / "Roaming"))
        return Path(base) / APP / "config.json"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP / "config.json"
    return _home() / ".config" / APP / "config.json"


def legacy_paths() -> list[Path]:
    out = []
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or (str(_home() / "AppData" / "Roaming"))
        out.append(Path(base) / "ear" / "config.json")
    else:
        out.append(_home() / ".config" / "ear" / "config.json")
    out.append(_home() / ".bailian" / "config.json")
    return out


def load(path: Path | None = None) -> dict[str, Any]:
    p = path or config_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save(data: dict[str, Any], path: Path | None = None) -> Path:
    p = path or config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if not sys.platform.startswith("win"):
        try:
            p.parent.chmod(0o700)
        except OSError:
            pass
    fd, tmp = tempfile.mkstemp(prefix=".config-", suffix=".json", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, p)
    finally:
        try:
            Path(tmp).unlink(missing_ok=True)
        except OSError:
            pass
    if not sys.platform.startswith("win"):
        try:
            p.chmod(0o600)
        except OSError:
            pass
    return p


def _base_from(data: dict[str, Any]) -> str:
    return str(data.get("base_url") or data.get("base") or "").strip().rstrip("/")


def _qwen_from(data: dict[str, Any]) -> dict[str, Any]:
    q = data.get("qwen")
    if isinstance(q, dict):
        return q
    # legacy flat config
    if data.get("api_key"):
        return {"api_key": data.get("api_key"), "base_url": data.get("base_url")}
    return {}


def get_qwen() -> dict[str, Any]:
    """Return api_key/base_url/source/models using documented precedence."""
    env_key = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    env_base = (os.environ.get("DASHSCOPE_BASE_URL") or "").strip()
    if env_key:
        return {"api_key": env_key, "base_url": env_base or DEFAULT_BASE,
                "source": "env", "omni_model": DEFAULT_OMNI, "asr_model": DEFAULT_ASR}
    # agent-ear native config
    data = load()
    q = _qwen_from(data)
    key = str(q.get("api_key") or "").strip()
    if key:
        return {"api_key": key, "base_url": _base_from(q) or DEFAULT_BASE,
                "source": "agent-ear-config",
                "omni_model": q.get("omni_model") or DEFAULT_OMNI,
                "asr_model": q.get("asr_model") or DEFAULT_ASR}
    # legacy ear config / bailian config
    for p in legacy_paths():
        d = load(p)
        q = _qwen_from(d)
        key = str(q.get("api_key") or "").strip()
        if key:
            return {"api_key": key, "base_url": _base_from(q) or DEFAULT_BASE,
                    "source": ("ear-config" if p.name == "config.json" and p.parent.name == "ear"
                               else "bailian-config"),
                    "omni_model": q.get("omni_model") or DEFAULT_OMNI,
                    "asr_model": q.get("asr_model") or DEFAULT_ASR}
    return {"api_key": "", "base_url": DEFAULT_BASE, "source": "unset",
            "omni_model": DEFAULT_OMNI, "asr_model": DEFAULT_ASR}


def save_qwen(api_key: str, base_url: str | None = None,
              omni_model: str | None = None, asr_model: str | None = None) -> Path:
    data = load()
    q = _qwen_from(data) if isinstance(data.get("qwen"), dict) else {}
    q.update({"api_key": api_key,
              "base_url": (base_url or q.get("base_url") or DEFAULT_BASE).rstrip("/"),
              "omni_model": omni_model or q.get("omni_model") or DEFAULT_OMNI,
              "asr_model": asr_model or q.get("asr_model") or DEFAULT_ASR})
    data["qwen"] = q
    return save(data)


def mask(key: str) -> str:
    if not key:
        return "(not configured)"
    return "****" + key[-4:] if len(key) >= 8 else "****"


def normalize_url(base: str, suffix: str) -> str:
    import re
    b = (base or DEFAULT_BASE).strip().rstrip("/")
    b = re.sub(r"/(?:api/v1|compatible-mode/v1)$", "", b)
    return b + suffix


def asr_base() -> str:
    return normalize_url(get_qwen()["base_url"], "/api/v1")


def omni_base() -> str:
    return normalize_url(get_qwen()["base_url"], "/compatible-mode/v1")


def text_base() -> str:
    return normalize_url(get_qwen()["base_url"], "/compatible-mode/v1")


def check_qwen(api_key: str | None = None, base_url: str | None = None,
               timeout: float = 20) -> dict[str, Any]:
    """Cheap key check; never returns the key."""
    import requests
    q = get_qwen()
    key = api_key or q.get("api_key") or ""
    base = (base_url or q.get("base_url") or DEFAULT_BASE).rstrip("/")
    url = normalize_url(base, "/compatible-mode/v1/models")
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
    except Exception as exc:
        return {"ok": False, "status": None, "error": type(exc).__name__}
    if r.status_code in (401, 403):
        return {"ok": False, "status": r.status_code, "error": "unauthorized"}
    if r.status_code == 200:
        return {"ok": True, "status": 200}
    return {"ok": False, "status": r.status_code, "error": "non-200"}
