from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_installer_is_china_first():
    s = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "mirrors.aliyun.com/pypi" in s
    assert "gh-proxy.com" in s
    assert "hf-mirror.com" in s
    assert "--noproxy" in s
    assert "UV_PYTHON_INSTALL_MIRROR" in s
    assert "uv tool install --force --default-index" in s
    assert "agent-ear[local]" not in s or "WithLocal" in s


def test_unix_installer_is_china_first():
    s = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "mirrors.aliyun.com/pypi" in s
    assert "pypi.tuna.tsinghua.edu.cn" in s
    assert "UV_PYTHON_INSTALL_MIRROR" in s
    assert "HF_ENDPOINT" in s


def test_skill_wrappers_offer_uvx_bootstrap():
    for name in ("agent-ear", "agent-ear.cmd", "agent-ear.ps1"):
        s = (ROOT / "skills" / "agent-ear" / "scripts" / name).read_text(encoding="utf-8")
        assert "uvx" in s
