@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo NecroCore Bug Tracker v1.2 - WEB ONLY Update
echo ------------------------------------------------------
if not exist "%ROOT%tools\upgrade_dashboard_v12.py" goto missing
call "%ROOT%tools\find_python.cmd"
if errorlevel 1 goto failed
"%NECRO_PY%" "%ROOT%tools\upgrade_dashboard_v12.py"
if errorlevel 1 goto failed
pause
exit /b 0
:missing
echo ERROR: Extract all files from v1.2 ZIP first.
:failed
pause
exit /b 1
