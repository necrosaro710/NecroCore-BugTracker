@echo off
setlocal
if not exist "%~dp0client_private_config.json" (
  echo Run setup first.
  pause
  exit /b 1
)
wscript.exe "%~dp0install_autostart.vbs"
