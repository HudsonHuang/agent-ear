$ErrorActionPreference = "Stop"
Write-Host "agent-ear installer"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "uv not found. Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
}
uv tool install --force "agent-ear"
$cmd = Get-Command agent-ear -ErrorAction SilentlyContinue
if ($cmd) { $bin = $cmd.Source } else { $bin = Join-Path $env:USERPROFILE ".local\bin\agent-ear.exe" }
if ($Host.Name -eq "ConsoleHost" -and -not [Console]::IsInputRedirected -and (Test-Path $bin)) {
  & $bin setup
} else {
  Write-Host "Installed. Run: agent-ear setup"
}
