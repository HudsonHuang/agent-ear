$ErrorActionPreference = "Stop"
if ($env:AGENT_EAR_BIN) {
  & $env:AGENT_EAR_BIN @args
  exit $LASTEXITCODE
}
if (-not (Get-Command agent-ear -ErrorAction SilentlyContinue)) {
  @(
    "agent-ear CLI not found on PATH.",
    "This skill is a thin wrapper; install the CLI first:",
    "  uv tool install agent-ear",
    "  pipx install agent-ear",
    "  python -m pip install --user agent-ear"
  ) | ForEach-Object { [Console]::Error.WriteLine($_) }
  exit 127
}
& agent-ear @args
exit $LASTEXITCODE
