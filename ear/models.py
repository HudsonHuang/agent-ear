"""Model manager: atomic, resumable, checksummed downloads.

No wget. Uses requests (honours HTTPS_PROXY / HTTP_PROXY). Models live in
~/.cache/ear/models unless EAR_MODEL_DIR is set.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests

DEFAULT_DIR = Path.home() / ".cache" / "ear" / "models"
PANNS_HOME = Path.home() / "panns_data"
TORCH_CACHE = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
BUNDLED_LABELS = Path(__file__).parent / "_data" / "models" / "class_labels_indices.csv"


def hf_endpoint() -> str:
    """China-first HF endpoint; override with HF_ENDPOINT/EAR_HF_ENDPOINT."""
    import os
    return (os.environ.get("EAR_HF_ENDPOINT") or os.environ.get("HF_ENDPOINT")
            or "https://hf-mirror.com").rstrip("/")


def _hf(path: str) -> str:
    return f"{hf_endpoint()}/{path.lstrip('/')}"


@dataclass(frozen=True)
class ModelSpec:
    name: str
    filename: str
    url: str
    size: int
    sha256: str | None = None
    alt_urls: tuple[str, ...] = ()


MODELS: dict[str, ModelSpec] = {
    "psed_beats": ModelSpec(
        name="psed_beats",
        filename="BEATs_strong_1.pt",
        url="https://gh-proxy.com/https://github.com/fschmid56/PretrainedSED/releases/download/v0.0.1/BEATs_strong_1.pt",
        size=364_091_999,
        alt_urls=(
            "https://github.com/fschmid56/PretrainedSED/releases/download/v0.0.1/BEATs_strong_1.pt",
        ),
    ),
    "panns_clip": ModelSpec(
        name="panns_clip",
        filename="Cnn14_mAP=0.431.pth",
        url=_hf("thelou1s/panns-inference/resolve/main/Cnn14_mAP%3D0.431.pth"),
        size=327_428_481,
        alt_urls=(
            "https://huggingface.co/thelou1s/panns-inference/resolve/main/Cnn14_mAP%3D0.431.pth",
            "https://hf-mirror.com/thelou1s/panns-inference/resolve/main/Cnn14_mAP%3D0.431.pth",
        ),
    ),
    "panns_labels": ModelSpec(
        name="panns_labels",
        filename="class_labels_indices.csv",
        url="https://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/class_labels_indices.csv",
        size=14_675,
        alt_urls=(
            "https://hf-mirror.com/datasets/agkphysics/AudioSet/resolve/main/class_labels_indices.csv",
        ),
    ),
    "beat_this_small0": ModelSpec(
        name="beat_this_small0",
        filename="small0.ckpt",
        url="https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/small0.ckpt",
        size=8_451_101,
    ),
}


class ModelError(RuntimeError):
    pass


def model_dir() -> Path:
    raw = os.environ.get("EAR_MODEL_DIR")
    return Path(raw).expanduser() if raw else DEFAULT_DIR


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _proxies() -> dict[str, str] | None:
    raw = os.environ.get("EAR_DOWNLOAD_PROXY") or os.environ.get("HTTPS_PROXY") \
        or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") \
        or os.environ.get("http_proxy")
    if not raw:
        return None
    return {"http": raw, "https": raw}


def _valid(path: Path, spec: ModelSpec) -> bool:
    if not path.is_file() or path.stat().st_size != spec.size:
        return False
    if spec.sha256 and _sha256(path) != spec.sha256:
        return False
    return True


def _download(spec: ModelSpec, dest: Path, *, retries: int = 4) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    urls = (spec.url,) + spec.alt_urls
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        for url in urls:
            try:
                existing = part.stat().st_size if part.is_file() else 0
                if existing > spec.size:
                    part.unlink()
                    existing = 0
                headers = {"Range": f"bytes={existing}-"} if existing else {}
                with requests.get(url, headers=headers, stream=True, timeout=120,
                                  allow_redirects=True, proxies=_proxies()) as r:
                    if r.status_code == 416 and existing == spec.size:
                        break
                    if r.status_code not in (200, 206):
                        raise ModelError(f"HTTP {r.status_code} for {url}")
                    mode = "ab" if existing and r.status_code == 206 else "wb"
                    if mode == "wb" and existing:
                        existing = 0
                    with part.open(mode) as f:
                        for chunk in r.iter_content(chunk_size=1 << 20):
                            if chunk:
                                f.write(chunk)
                if part.stat().st_size == spec.size:
                    os.replace(part, dest)
                    return dest
                raise ModelError(
                    f"incomplete download for {spec.name}: "
                    f"{part.stat().st_size}/{spec.size} bytes")
            except Exception as exc:  # retry other URL / backoff
                last = exc
                time.sleep(min(2 ** attempt, 8))
        if part.is_file() and part.stat().st_size == spec.size:
            os.replace(part, dest)
            return dest
    raise ModelError(f"failed to download {spec.name}: {last}")


def ensure_model(name: str, *, check_only: bool = False) -> Path | None:
    if name not in MODELS:
        raise ModelError(f"unknown model: {name}")
    spec = MODELS[name]
    dest = model_dir() / spec.filename

    # Beat This! may already be in torch's hub cache from a previous run.
    if name == "beat_this_small0":
        cached = TORCH_CACHE / "beat_this-small0.ckpt"
        if _valid(cached, spec):
            return cached if check_only else cached

    if _valid(dest, spec):
        return dest
    if check_only:
        return None
    return _download(spec, dest)


def ensure_models(names: tuple[str, ...] | list[str]) -> dict[str, Path]:
    """Download independent models concurrently (fewer round trips, faster)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    unique = list(dict.fromkeys(names))
    out: dict[str, Path] = {}
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(unique)))) as pool:
        futs = {pool.submit(ensure_model, n): n for n in unique}
        for fut in as_completed(futs):
            name = futs[fut]
            path = fut.result()
            if path is not None:
                out[name] = path
    return out


def ensure_panns_labels() -> Path:
    """panns_inference imports labels from ~/panns_data at import time."""
    PANNS_HOME.mkdir(parents=True, exist_ok=True)
    dst = PANNS_HOME / "class_labels_indices.csv"
    spec = MODELS["panns_labels"]
    if _valid(dst, spec):
        return dst
    # Labels are tiny and stable; ship them so basic/local never touches Google.
    if BUNDLED_LABELS.is_file() and _valid(BUNDLED_LABELS, spec):
        dst.write_bytes(BUNDLED_LABELS.read_bytes())
        return dst
    src = ensure_model("panns_labels")
    assert src is not None
    dst.write_bytes(src.read_bytes())
    return dst


def status() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name, spec in MODELS.items():
        dest = model_dir() / spec.filename
        if name == "beat_this_small0":
            cached = TORCH_CACHE / "beat_this-small0.ckpt"
            if _valid(cached, spec):
                dest = cached
        if name == "panns_labels":
            legacy = PANNS_HOME / spec.filename
            if _valid(legacy, spec):
                dest = legacy
        ok = _valid(dest, spec)
        out[name] = {
            "path": str(dest),
            "exists": dest.is_file(),
            "size": dest.stat().st_size if dest.is_file() else 0,
            "expected_size": spec.size,
            "valid": ok,
        }
    return out
