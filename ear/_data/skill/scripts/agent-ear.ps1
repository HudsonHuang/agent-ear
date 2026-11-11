$ErrorActionPreference = "Stop"
if ($env:AGENT_EAR_BIN) {
  & $env:AGENT_EAR_BIN @args
} else {
  & agent-ear @args
}
exit $LASTEXITCODE
