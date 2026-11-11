"""Find or install a local ffmpeg/ffprobe, China-first.

The Windows path avoids winget/choco (slow, often blocked) and uses a direct
static build zip with the GitHub proxy as a fallback.  Downloads can go through
a corporate proxy, but the sources are China-reachable mirrors.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from . import media

# gyan.dev is small (~35 MB) and usually reachable from China; the BtbN build
# is larger but has a working gh-proxy mirror.
WIN_URLS = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://gh-proxy.com/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
)


def local_bin_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData/Local"))
        return base / "agent-ear" / "ffmpeg" / "bin"
    return Path.home() / ".local" / "share" / "agent-ear" / "ffmpeg" / "bin"


def find_bins() -> tuple[str | None, str | None]:
    """Return (ffmpeg, ffprobe) from env, local install, or PATH."""
    env_ff = os.environ.get("FFMPEG_BIN")
    env_fp = os.environ.get("FFPROBE_BIN")
    if env_ff and env_fp and Path(env_ff).is_file() and Path(env_fp).is_file():
        return env_ff, env_fp
    local = local_bin_dir()
    for names in (("ffmpeg.exe", "ffprobe.exe"), ("ffmpeg", "ffprobe")):
        ff, fp = local / names[0], local / names[1]
        if ff.is_file() and fp.is_file():
            return str(ff), str(fp)
    return shutil.which("ffmpeg"), shutil.which("ffprobe")


def apply() -> tuple[str | None, str | None]:
    ff, fp = find_bins()
    if ff and fp:
        os.environ.setdefault("FFMPEG_BIN", ff)
        os.environ.setdefault("FFPROBE_BIN", fp)
        media.refresh(ff, fp)
    return ff, fp


def _download(url: str, dest: Path) -> None:
    import requests
    print(f"  downloading {url}", file=sys.stderr, flush=True)
    with requests.get(url, stream=True, timeout=(30, 1800),
                      proxies=_proxies(url), allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        done = 0
        last = 0.0
        with dest.open("wb") as f:
            for chunk in r.iter_content(1 << 20):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                now = time.time()
                if now - last >= 2:
                    pct = f"{done * 100 // total}%" if total else f"{done / 1e6:.1f} MB"
                    print(f"  {pct}", file=sys.stderr, flush=True)
                    last = now


def _proxies(url: str = "") -> dict[str, str] | None:
    explicit = os.environ.get("EAR_DOWNLOAD_PROXY")
    if explicit:
        return {"http": explicit, "https": explicit}
    host = (url.split("/")[2] if "://" in url else "").lower()
    if host in ("gh-proxy.com", "mirrors.ustc.edu.cn") or host.endswith(".gh-proxy.com"):
        return None
    raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    return {"http": raw, "https": raw} if raw else None


def install_windows() -> tuple[str, str]:
    """Download a static Windows build into %LOCALAPPDATA%\\agent-ear."""
    if not sys.platform.startswith("win"):
        raise RuntimeError("automatic ffmpeg install is Windows-only; use brew/apt")
    bin_dir = local_bin_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    with tempfile.TemporaryDirectory(prefix="agent-ear-ffmpeg-") as td:
        td_path = Path(td)
        for url in WIN_URLS:
            zip_path = td_path / "ffmpeg.zip"
            try:
                _download(url, zip_path)
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(td_path / "unpack")
                ff = next((p for p in (td_path / "unpack").rglob("ffmpeg.exe")), None)
                fp = next((p for p in (td_path / "unpack").rglob("ffprobe.exe")), None)
                if not ff or not fp:
                    raise RuntimeError("zip did not contain ffmpeg.exe/ffprobe.exe")
                shutil.copy2(ff, bin_dir / "ffmpeg.exe")
                shutil.copy2(fp, bin_dir / "ffprobe.exe")
                ff_dst, fp_dst = bin_dir / "ffmpeg.exe", bin_dir / "ffprobe.exe"
                os.environ["FFMPEG_BIN"] = str(ff_dst)
                os.environ["FFPROBE_BIN"] = str(fp_dst)
                if str(bin_dir) not in os.environ.get("PATH", "").split(os.pathsep):
                    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH','')}"
                media.refresh(str(ff_dst), str(fp_dst))
                return str(ff_dst), str(fp_dst)
            except Exception as exc:  # try next mirror
                last = exc
                print(f"  failed: {exc}", file=sys.stderr, flush=True)
                zip_path.unlink(missing_ok=True)
    raise RuntimeError(f"could not install ffmpeg: {last}")
