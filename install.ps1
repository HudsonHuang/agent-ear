param(
  [switch]$WithLocal,
  [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

# China-first defaults. Even behind a VPN we prefer these (faster, cheaper).
$PipMirror = "https://mirrors.aliyun.com/pypi/simple"
$PipMirror2 = "https://pypi.tuna.tsinghua.edu.cn/simple"
$HfMirror = "https://hf-mirror.com"
$UvArch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64" } else { "x86_64" }
$UvZip = "https://mirrors.ustc.edu.cn/github-release/astral-sh/uv/LatestRelease/uv-$UvArch-pc-windows-msvc.zip"
$PyMirror = "https://mirrors.ustc.edu.cn/github-release/astral-sh/python-build-standalone/"
$FfmpegSources = @(
  "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
  "https://gh-proxy.com/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
  "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
)

function Write-Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Add-Path($p) {
  if ($p -and (Test-Path $p) -and ($env:Path -notlike "*$p*")) { $env:Path = "$p;$env:Path" }
}
function Find-Exe($name) {
  $c = Get-Command $name -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return $null
}
function Invoke-Download($url, $dest) {
  New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
  $curl = Find-Exe "curl.exe"
  if ($curl) {
    # --noproxy keeps domestic mirrors direct even when a VPN system proxy is on.
    & $curl -L --fail --noproxy "*" --connect-timeout 20 --max-time 900 --retry 2 --retry-delay 2 -o $dest $url
    if ($LASTEXITCODE -eq 0 -and (Test-Path $dest) -and (Get-Item $dest).Length -gt 100000) { return }
    Remove-Item $dest -Force -ErrorAction SilentlyContinue
    & $curl -L --fail --connect-timeout 20 --max-time 900 --retry 2 -o $dest $url
    if ($LASTEXITCODE -eq 0 -and (Test-Path $dest) -and (Get-Item $dest).Length -gt 100000) { return }
  } else {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $dest -TimeoutSec 900
    if ((Test-Path $dest) -and (Get-Item $dest).Length -gt 100000) { return }
  }
  throw "download failed: $url"
}

Write-Host "agent-ear installer for native Windows (no WSL, China mirrors)" -ForegroundColor Green
Write-Host "PowerShell: $($PSVersionTable.PSVersion)  arch: $env:PROCESSOR_ARCHITECTURE"

# 1) ffmpeg / ffprobe: local zip first (much faster than winget), then winget.
Write-Step "1/4 ffmpeg / ffprobe"
$localBin = Join-Path $env:LOCALAPPDATA "agent-ear\ffmpeg\bin"
Add-Path $localBin
$ffmpeg = Find-Exe "ffmpeg"; $ffprobe = Find-Exe "ffprobe"
if (-not $ffmpeg -or -not $ffprobe) {
  $cache = Join-Path $env:LOCALAPPDATA "agent-ear\cache"
  New-Item -ItemType Directory -Force -Path $cache | Out-Null
  $localZips = @(Get-ChildItem $cache -Filter "ffmpeg*.zip" -ErrorAction SilentlyContinue)
  $installed = $false
  foreach ($zip in $localZips) {
    $unpack = $null
    try {
      $unpack = Join-Path $env:TEMP ("ae-ff-" + [guid]::NewGuid())
      Expand-Archive -Path $zip.FullName -DestinationPath $unpack -Force
      $ff = Get-ChildItem $unpack -Recurse -Filter ffmpeg.exe | Select-Object -First 1
      $fp = Get-ChildItem $unpack -Recurse -Filter ffprobe.exe | Select-Object -First 1
      if ($ff -and $fp) {
        New-Item -ItemType Directory -Force -Path $localBin | Out-Null
        Copy-Item $ff.FullName (Join-Path $localBin "ffmpeg.exe") -Force
        Copy-Item $fp.FullName (Join-Path $localBin "ffprobe.exe") -Force
        $installed = $true; break
      }
    } catch { }
    finally { Remove-Item $unpack -Recurse -Force -ErrorAction SilentlyContinue }
  }
  if (-not $installed) {
    $i = 0
    foreach ($url in $FfmpegSources) {
      $i++
      $zipPath = Join-Path $cache ("ffmpeg-" + $i + ".zip")
      $unpack = $null
      try {
        Write-Host "  source $i/$($FfmpegSources.Count): $url" -ForegroundColor DarkGray
        Invoke-Download $url $zipPath
        $unpack = Join-Path $env:TEMP ("ae-ff-" + [guid]::NewGuid())
        Expand-Archive -Path $zipPath -DestinationPath $unpack -Force
        $ff = Get-ChildItem $unpack -Recurse -Filter ffmpeg.exe | Select-Object -First 1
        $fp = Get-ChildItem $unpack -Recurse -Filter ffprobe.exe | Select-Object -First 1
        if (-not $ff -or -not $fp) { throw "zip has no ffmpeg/ffprobe" }
        New-Item -ItemType Directory -Force -Path $localBin | Out-Null
        Copy-Item $ff.FullName (Join-Path $localBin "ffmpeg.exe") -Force
        Copy-Item $fp.FullName (Join-Path $localBin "ffprobe.exe") -Force
        $installed = $true
        break
      } catch { Write-Host "  failed: $($_.Exception.Message)" -ForegroundColor Yellow }
      finally { Remove-Item $unpack -Recurse -Force -ErrorAction SilentlyContinue }
    }
  }
  if (-not $installed) {
    $winget = Find-Exe "winget"
    if ($winget) {
      Write-Host "  zip failed; trying winget (might take a few minutes)..." -ForegroundColor Yellow
      try { & $winget install --id Gyan.FFmpeg -e --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity } catch { }
      Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "Gyan.FFmpeg*" } |
        ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue } |
        Select-Object -First 1 | ForEach-Object {
          New-Item -ItemType Directory -Force -Path $localBin | Out-Null
          Copy-Item (Join-Path $_.DirectoryName "*") $localBin -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
  }
  Add-Path $localBin
  $ffmpeg = Find-Exe "ffmpeg"; $ffprobe = Find-Exe "ffprobe"
}
if (-not $ffmpeg -or -not $ffprobe) {
  throw "ffmpeg/ffprobe not found. Re-run this installer, or install: winget install Gyan.FFmpeg"
}
$env:FFMPEG_BIN = $ffmpeg; $env:FFPROBE_BIN = $ffprobe
Write-Host "ffmpeg: $ffmpeg"

# 2) uv: existing -> pip mirror -> USTC binary zip -> official installer.
Write-Step "2/4 uv"
$uv = Find-Exe "uv"
if (-not $uv) {
  foreach ($py in @("python", "py")) {
    $pyExe = Find-Exe $py
    if (-not $pyExe) { continue }
    try {
      Write-Host "  pip mirror: installing uv" -ForegroundColor DarkGray
      if ($py -eq "py") { & $pyExe -3 -m pip install --user --index-url $PipMirror uv }
      else { & $pyExe -m pip install --user --index-url $PipMirror uv }
      $uv = Find-Exe "uv"
      if (-not $uv) {
        $cand = Get-ChildItem "$env:APPDATA\Python" -Recurse -Filter uv.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cand) { $uv = $cand.FullName }
      }
      if ($uv) { break }
    } catch { Write-Host "  pip uv failed: $($_.Exception.Message)" -ForegroundColor Yellow }
  }
}
if (-not $uv) {
  $zip = Join-Path $env:TEMP "uv-windows.zip"
  $dest = Join-Path $env:LOCALAPPDATA "agent-ear\uv"
  try {
    Write-Host "  USTC mirror: uv binary" -ForegroundColor DarkGray
    Invoke-Download $UvZip $zip
    Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    $cand = Get-ChildItem $dest -Recurse -Filter uv.exe | Select-Object -First 1
    if ($cand) { $uv = $cand.FullName }
  } catch { Write-Host "  uv zip failed: $($_.Exception.Message)" -ForegroundColor Yellow }
}
if (-not $uv) {
  Write-Host "  official installer fallback..." -ForegroundColor Yellow
  try {
    Invoke-Expression (Invoke-RestMethod "https://astral.sh/uv/install.ps1")
    $candidate = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path $candidate) { $uv = $candidate }
  } catch { }
}
if (-not $uv) { throw "uv not found. Install: winget install astral-sh.uv, then reopen PowerShell." }
Add-Path (Split-Path $uv)
Write-Host "uv: $uv"

# 3) agent-ear: domestic PyPI first; no forced Python download.
Write-Step "3/4 agent-ear"
$env:UV_DEFAULT_INDEX = $PipMirror
$env:UV_PYTHON_INSTALL_MIRROR = $PyMirror
$env:HF_ENDPOINT = $HfMirror
$spec = if ($WithLocal) { "agent-ear[local]" } else { "agent-ear" }
$ok = $false
foreach ($idx in @($PipMirror, $PipMirror2, "https://pypi.org/simple")) {
  Write-Host "  index: $idx" -ForegroundColor DarkGray
  & $uv tool install --force --default-index $idx $spec
  if ($LASTEXITCODE -eq 0) { $ok = $true; break }
  Write-Host "  failed; trying next index" -ForegroundColor Yellow
}
if (-not $ok) { throw "uv tool install failed" }

try { $toolBin = (& $uv tool dir --bin 2>$null); if ($toolBin) { Add-Path $toolBin } } catch {}
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

# 4) DSH skill + optional key setup. Models are NOT downloaded here: basic only
# needs Qwen; precise/events download only when the user actually asks for them.
Write-Step "4/4 DSH skill"
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
    Write-Host "  `"$agent`" setup --target dsh --install-ffmpeg"
  }
}

Write-Step "verify"
& $agent doctor --json
if ($LASTEXITCODE -ne 0) { Write-Host "doctor returned non-zero; inspect output above" -ForegroundColor Yellow }
$dshHome = if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE ".dsh" }
$skill = Join-Path $dshHome "skills\agent-ear\SKILL.md"
if (Test-Path $skill) { Write-Host "DSH skill: $skill" -ForegroundColor Green }
else { Write-Host "DSH skill not found at $skill" -ForegroundColor Yellow }

Write-Host "`nDone. Next: open a new DSH session and invoke /agent-ear." -ForegroundColor Green
Write-Host "Models: basic downloads none; precise/events download on first use from hf-mirror/gh-proxy." -ForegroundColor DarkGray
if (-not $SkipSetup) {
  $cfg = Join-Path $env:APPDATA "agent-ear\config.json"
  if (-not (Test-Path $cfg) -and -not $env:DASHSCOPE_API_KEY) {
    Write-Host "If key setup was skipped: run  `"$agent`" setup --target dsh  in a terminal." -ForegroundColor Yellow
    exit 10
  }
}
exit 0
