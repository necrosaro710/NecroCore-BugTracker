@echo off
setlocal
title NecroCore Screenshot Client - Read Only Check
if not exist "%~dp0runtime\python.exe" (
  echo Run setup first.
  pause
  exit /b 1
)
"%~dp0runtime\python.exe" "%~dp0necro_screenshot_client.py" --check
echo.
echo This check does NOT copy or upload screenshots.
pause
