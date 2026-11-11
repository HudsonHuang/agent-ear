"""The release version lives in pyproject.toml; mirrored manifests must match."""
from __future__ import annotations

import json
import re
from pathlib import Path

import ear

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project = text.split("[project]", 1)[1].split("\n[", 1)[0]
    match = re.search(r'^version = "([^"]+)"$', project, re.MULTILINE)
    assert match, "pyproject.toml [project] has no static version"
    return match.group(1)


def test_package_version_matches_pyproject():
    assert ear.__version__ == _pyproject_version()


def test_plugin_manifest_version_matches_pyproject():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == _pyproject_version()


def test_npm_manifest_version_matches_pyproject():
    """The DSH bundle lives in package.json; it must ship the same version."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == _pyproject_version()


def test_npm_manifest_declares_a_non_empty_bundle_patch():
    """awesome-dsh-plugin rejects a DSH package without dsh.bundle.patch."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    patch = pkg.get("dsh", {}).get("bundle", {}).get("patch")
    assert patch, "package.json needs dsh.bundle.patch"
    target = ROOT / patch
    assert target.is_file(), f"{patch} does not exist"
    assert target.read_text(encoding="utf-8").strip(), f"{patch} is empty"
