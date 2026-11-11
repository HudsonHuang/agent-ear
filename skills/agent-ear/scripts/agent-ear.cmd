@echo off
setlocal
if not "%AGENT_EAR_BIN%"=="" (
  "%AGENT_EAR_BIN%" %*
) else (
  agent-ear %*
)
exit /b %ERRORLEVEL%
