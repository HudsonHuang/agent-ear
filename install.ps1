param(
  [switch]$WithLocal,
  [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

function Write-Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Add-Path($p) {
  if ($p -and (Test-Path $p) -and ($env:Path -notlike "*$p*")) { $env:Path = "$p;$env:Path" }
}
function Find-Exe($name) {
  $c = Get-Command $name -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return $null
}

Write-Host "agent-ear installer for native Windows (no WSL required)" -ForegroundColor Green
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"

# 1) ffmpeg / ffprobe
Write-Step "checking ffmpeg / ffprobe"
$ffmpeg = Find-Exe "ffmpeg"
$ffprobe = Find-Exe "ffprobe"
if (-not $ffmpeg -or -not $ffprobe) {
  $winget = Find-Exe "winget"
  if ($winget) {
    Write-Host "trying: winget install Gyan.FFmpeg"
    try {
      & $winget install --id Gyan.FFmpeg -e --source winget --accept-package-agreements --accept-source-agreements
    } catch { Write-Host "winget install failed: $_" -ForegroundColor Yellow }
    Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like "Gyan.FFmpeg*" } |
      ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue } |
      Select-Object -First 1 | ForEach-Object { Add-Path $_.DirectoryName }
    $ffmpeg = Find-Exe "ffmpeg"; $ffprobe = Find-Exe "ffprobe"
  }
  if (-not $ffmpeg -or -not $ffprobe) {
    $choco = Find-Exe "choco"
    if ($choco) {
      Write-Host "trying: choco install ffmpeg -y"
      try { & $choco install ffmpeg -y --no-progress } catch { Write-Host "choco failed: $_" -ForegroundColor Yellow }
      $ffmpeg = Find-Exe "ffmpeg"; $ffprobe = Find-Exe "ffprobe"
    }
  }
  if (-not $ffmpeg -or -not $ffprobe) {
    Write-Host "falling back to a user-local ffmpeg zip (no admin)" -ForegroundColor Yellow
    $root = Join-Path $env:LOCALAPPDATA "agent-ear"
    $zip = Join-Path $env:TEMP "ffmpeg-essentials.zip"
    $dest = Join-Path $root "ffmpeg"
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    if (-not (Test-Path $dest)) {
      Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
      Expand-Archive -Path $zip -DestinationPath $root -Force
      Get-ChildItem $root -Directory -Filter "ffmpeg-*" | Select-Object -First 1 | ForEach-Object { Move-Item $_.FullName $dest -Force }
      Remove-Item $zip -Force -ErrorAction SilentlyContinue
    }
    $bin = Get-ChildItem $dest -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
      Select-Object -First 1 | ForEach-Object { $_.DirectoryName }
    Add-Path $bin
    $ffmpeg = Find-Exe "ffmpeg"; $ffprobe = Find-Exe "ffprobe"
  }
}
if (-not $ffmpeg -or -not $ffprobe) {
  throw "ffmpeg/ffprobe not found. Install manually: winget install Gyan.FFmpeg, then reopen PowerShell."
}
Write-Host "ffmpeg: $ffmpeg"

# 2) uv
Write-Step "checking uv"
$uv = Find-Exe "uv"
if (-not $uv) {
  $winget = Find-Exe "winget"
  if ($winget) {
    Write-Host "trying: winget install astral-sh.uv"
    try { & $winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements } catch { Write-Host "winget uv failed: $_" -ForegroundColor Yellow }
    $uv = Find-Exe "uv"
    if (-not $uv) {
      $candidate = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
      if (Test-Path $candidate) { $uv = $candidate }
    }
  }
  if (-not $uv) {
    Write-Host "trying official uv installer"
    Invoke-Expression (Invoke-RestMethod "https://astral.sh/uv/install.ps1")
    $candidate = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path $candidate) { $uv = $candidate }
  }
}
if (-not $uv) { throw "uv not found. Install: winget install astral-sh.uv, then reopen PowerShell." }
Add-Path (Split-Path $uv)
Write-Host "uv: $uv"

# 3) install agent-ear from PyPI
Write-Step "installing agent-ear"
$spec = if ($WithLocal) { "agent-ear[local]==0.2.1" } else { "agent-ear==0.2.1" }
& $uv tool install --python 3.12 --force $spec
if ($LASTEXITCODE -ne 0) { throw "uv tool install failed" }

$agent = Find-Exe "agent-ear"
if (-not $agent) {
  $candidate = Join-Path $env:USERPROFILE ".local\bin\agent-ear.exe"
  if (Test-Path $candidate) { $agent = $candidate }
}
if (-not $agent) { throw "agent-ear.exe not found after install" }
Add-Path (Split-Path $agent)
Write-Host "agent-ear: $agent"
& $agent --version
if ($LASTEXITCODE -ne 0) { throw "agent-ear --version failed" }

# 4) install DSH skill; setup if a key is already available
Write-Step "installing DSH skill"
& $agent skill install --target dsh --force
if ($LASTEXITCODE -ne 0) { throw "DSH skill install failed" }

if (-not $SkipSetup) {
  $hasKey = [bool]$env:DASHSCOPE_API_KEY
  if (-not $hasKey) {
    $cfg = Join-Path $env:APPDATA "agent-ear\config.json"
    $hasKey = Test-Path $cfg
  }
  if ($hasKey) {
    Write-Host "key detected; running non-interactive setup"
    & $agent setup --target dsh --non-interactive --skip-key --skip-api-check --force
  } else {
    Write-Host ""
    Write-Host "No Qwen API key detected." -ForegroundColor Yellow
    Write-Host "Run this in a NEW PowerShell window (hidden input, do not paste the key into DSH chat):" -ForegroundColor Yellow
    Write-Host "  `"$agent`" setup --target dsh"
  }
}

# 5) verify
Write-Step "verify"
& $agent doctor --json
if ($LASTEXITCODE -ne 0) { Write-Host "doctor returned non-zero; inspect output above" -ForegroundColor Yellow }
$dshHome = if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE ".dsh" }
$skill = Join-Path $dshHome "skills\agent-ear\SKILL.md"
if (Test-Path $skill) { Write-Host "DSH skill: $skill" -ForegroundColor Green }
else { Write-Host "DSH skill not found at $skill" -ForegroundColor Yellow }

Write-Host "`nDone. Next: open a new DSH session and invoke /agent-ear." -ForegroundColor Green
if (-not $SkipSetup) {
  $cfg = Join-Path $env:APPDATA "agent-ear\config.json"
  if (-not (Test-Path $cfg) -and -not $env:DASHSCOPE_API_KEY) {
    Write-Host "If key setup was skipped: run  `"$agent`" setup --target dsh  in a terminal." -ForegroundColor Yellow
    exit 10
  }
}
exit 0
