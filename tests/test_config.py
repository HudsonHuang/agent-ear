import json
import stat
from pathlib import Path

from ear import config


def test_env_config_path_and_precedence(tmp_path, monkeypatch):
    p = tmp_path / "cfg.json"
    monkeypatch.setenv("AGENT_EAR_CONFIG", str(p))
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-env")
    q = config.get_qwen()
    assert q["api_key"] == "sk-env"
    assert q["source"] == "env"
    config.save_qwen("sk-file", "https://example.com")
    monkeypatch.delenv("DASHSCOPE_API_KEY")
    q = config.get_qwen()
    assert q["api_key"] == "sk-file"
    assert q["base_url"] == "https://example.com"
    data = json.loads(p.read_text())
    assert data["qwen"]["api_key"] == "sk-file"
    if not config.sys.platform.startswith("win"):
        assert stat.S_IMODE(p.stat().st_mode) == 0o600


def test_base_normalization():
    assert config.normalize_url("https://x.test", "/api/v1") == "https://x.test/api/v1"
    assert config.normalize_url("https://x.test/api/v1", "/compatible-mode/v1") == "https://x.test/compatible-mode/v1"
    assert config.normalize_url("https://x.test/compatible-mode/v1", "/api/v1") == "https://x.test/api/v1"


def test_mask():
    assert config.mask("") == "(not configured)"
    assert config.mask("sk-1234567890").endswith("7890")
    assert "sk-1234567890" not in config.mask("sk-1234567890")


def test_windows_appdata_path(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.delenv("AGENT_EAR_CONFIG", raising=False)
    assert config.config_path() == tmp_path / "agent-ear" / "config.json"
