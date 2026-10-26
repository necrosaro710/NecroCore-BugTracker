@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo.
echo NecroCore Bug Tracker v1.1 - WEB ONLY Update
 echo ------------------------------------------------------
if not exist "%ROOT%tools\upgrade_dashboard_v11.py" (
  echo ERROR: Extract ALL files from the v1.1 ZIP first.
  goto failed
)
call "%ROOT%tools\find_python.cmd"
if errorlevel 1 goto failed
if not defined NECRO_PY goto failed
"%NECRO_PY%" "%ROOT%tools\upgrade_dashboard_v11.py"
if errorlevel 1 goto failed
pause
exit /b 0
:failed
echo.
echo No database/worldserver modification requested.
pause
exit /b 1
