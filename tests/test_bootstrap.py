from pathlib import Path

from ear import ffmpeg_boot, models


def test_hf_endpoint_override(monkeypatch):
    monkeypatch.setenv("EAR_HF_ENDPOINT", "https://example.cn/hf/")
    assert models.hf_endpoint() == "https://example.cn/hf"
    assert models._hf("repo/file") == "https://example.cn/hf/repo/file"


def test_bundled_panns_labels_are_complete():
    p = models.BUNDLED_LABELS
    assert p.is_file()
    data = p.read_bytes().replace(b"\r\n", b"\n")
    assert len(data) == models.MODELS["panns_labels"].size


def test_psed_has_china_fallback():
    spec = models.MODELS["psed_beats"]
    assert "gh-proxy.com" in spec.url
    assert any("github.com" in u for u in spec.alt_urls)


def test_ffmpeg_local_bin_preferred(tmp_path, monkeypatch):
    bin_dir = tmp_path / "ffmpeg" / "bin"
    bin_dir.mkdir(parents=True)
    ff, fp = bin_dir / "ffmpeg", bin_dir / "ffprobe"
    ff.write_text("#!/bin/sh\n")
    fp.write_text("#!/bin/sh\n")
    monkeypatch.setattr(ffmpeg_boot, "local_bin_dir", lambda: bin_dir)
    monkeypatch.delenv("FFMPEG_BIN", raising=False)
    monkeypatch.delenv("FFPROBE_BIN", raising=False)
    got_ff, got_fp = ffmpeg_boot.find_bins()
    assert got_ff == str(ff)
    assert got_fp == str(fp)


def test_domestic_mirror_bypasses_proxy(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7897")
    monkeypatch.delenv("EAR_DOWNLOAD_PROXY", raising=False)
    assert models._proxies("https://hf-mirror.com/repo/file") is None
    assert models._proxies("https://gh-proxy.com/https://github.com/a/b") is None
    assert models._proxies("https://cloud.cp.jku.at/file") is not None
