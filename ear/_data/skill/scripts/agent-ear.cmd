@echo off
setlocal
if not "%AGENT_EAR_BIN%"=="" (
  "%AGENT_EAR_BIN%" %*
  exit /b %ERRORLEVEL%
)
where agent-ear >nul 2>nul
if errorlevel 1 (
  where uvx >nul 2>nul
  if not errorlevel 1 (
    echo agent-ear CLI not installed; bootstrapping via uvx... 1>&2
    uvx --from agent-ear agent-ear %*
    exit /b %ERRORLEVEL%
  )
  echo agent-ear CLI not found on PATH. 1>&2
  echo This skill is a thin wrapper; install the CLI first: 1>&2
  echo   uv tool install agent-ear 1>&2
  echo   pipx install agent-ear 1>&2
  echo   python -m pip install --user agent-ear 1>&2
  exit /b 127
)
agent-ear %*
exit /b %ERRORLEVEL%
