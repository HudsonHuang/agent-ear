#!/usr/bin/env bash
set -euo pipefail
echo "agent-ear installer"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
uv tool install "agent-ear" || uv tool install --force "agent-ear"
BIN="$(command -v agent-ear || true)"
[ -n "$BIN" ] || BIN="$HOME/.local/bin/agent-ear"
if [ -t 0 ] && [ -x "$BIN" ]; then
  "$BIN" setup
else
  echo "Installed. Run: agent-ear setup"
fi
