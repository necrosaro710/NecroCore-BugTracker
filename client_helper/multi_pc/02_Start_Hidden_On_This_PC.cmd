@echo off
setlocal
if not exist "%~dp0client_private_config.json" (
  echo Please run 01_Setup_On_This_WoW_PC.cmd first.
  pause
  exit /b 1
)
if not exist "%~dp0runtime\pythonw.exe" (
  echo Portable Python runtime missing. Run setup again.
  pause
  exit /b 1
)
start "" "%SystemRoot%\System32\wscript.exe" "%~dp0launch_hidden.vbs"
echo Screenshot monitoring started silently on this WoW PC.
echo You may close this window.
