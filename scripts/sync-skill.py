#!/usr/bin/env python3
"""Sync the canonical skill into package data."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "skills" / "agent-ear"
dst = ROOT / "ear" / "_data" / "skill"
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print(f"synced {src} -> {dst}")
