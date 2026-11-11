#!/usr/bin/env bash
set -euo pipefail

# China-first installer: domestic PyPI default, HF mirror for models, USTC
# python-build-standalone mirror for uv-managed Python.
PIP_MIRROR="${PIP_MIRROR:-https://mirrors.aliyun.com/pypi/simple}"
PIP_MIRROR2="https://pypi.tuna.tsinghua.edu.cn/simple"
PY_MIRROR="https://mirrors.ustc.edu.cn/github-release/astral-sh/python-build-standalone/"
HF_MIRROR="${HF_ENDPOINT:-https://hf-mirror.com}"
# Keep domestic mirrors direct even when a VPN proxy is exported.
export NO_PROXY="mirrors.aliyun.com,pypi.tuna.tsinghua.edu.cn,mirrors.ustc.edu.cn,hf-mirror.com,gh-proxy.com,localhost,127.0.0.1${NO_PROXY:+,$NO_PROXY}"

echo "agent-ear installer (China mirrors)"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; trying domestic pip mirror..."
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user --index-url "$PIP_MIRROR" uv || true
  fi
  export PATH="$HOME/.local/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    echo "pip install uv failed; trying official installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || true
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

export UV_DEFAULT_INDEX="$PIP_MIRROR"
export UV_PYTHON_INSTALL_MIRROR="$PY_MIRROR"
export HF_ENDPOINT="$HF_MIRROR"

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    echo "ffmpeg missing; installing via Homebrew (may take a few minutes)..."
    brew install ffmpeg
  else
    echo "ffmpeg missing. Install it with: sudo apt install ffmpeg" >&2
    echo "Re-run this installer after that." >&2
    exit 2
  fi
fi

echo "installing agent-ear from domestic PyPI..."
ok=0
for idx in "$PIP_MIRROR" "$PIP_MIRROR2" "https://pypi.org/simple"; do
  echo "  index: $idx"
  if uv tool install --force --default-index "$idx" agent-ear; then ok=1; break; fi
done
[ "$ok" = 1 ] || { echo "uv tool install failed" >&2; exit 1; }

if [ "${AGENT_EAR_SKIP_SETUP:-0}" = "1" ]; then
  echo "Installed. Run: agent-ear setup"
  exit 0
fi

BIN="$(command -v agent-ear || true)"
[ -n "$BIN" ] || BIN="$HOME/.local/bin/agent-ear"
if [ -t 0 ] && [ -x "$BIN" ]; then
  "$BIN" setup
else
  echo "Installed. Run: agent-ear setup --install-ffmpeg"
fi
