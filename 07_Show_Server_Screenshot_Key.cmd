@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
if not exist "%ROOT%tools\show_screenshot_key.py" goto missing
call "%ROOT%tools\find_python.cmd"
if errorlevel 1 goto failed
"%NECRO_PY%" "%ROOT%tools\show_screenshot_key.py"
if errorlevel 1 goto failed
pause
exit /b 0
:missing
echo ERROR: Extract the whole v1.2 Community Edition ZIP first.
:failed
pause
exit /b 1
