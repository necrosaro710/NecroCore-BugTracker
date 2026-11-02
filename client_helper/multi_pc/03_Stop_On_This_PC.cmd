@echo off
setlocal
if not exist "%~dp0runtime\python.exe" (
  echo Not installed on this PC.
  pause
  exit /b 1
)
"%~dp0runtime\python.exe" "%~dp0necro_screenshot_client.py" --stop
echo The background client will exit within a few seconds.
pause
