@echo off
setlocal
title NecroCore Screenshot Client - One Transfer Pass
if not exist "%~dp0runtime\python.exe" (
  echo Run setup first.
  pause
  exit /b 1
)
"%~dp0runtime\python.exe" "%~dp0necro_screenshot_client.py" --once
echo.
echo This performs one scan, then exits. Local originals are retained.
pause
