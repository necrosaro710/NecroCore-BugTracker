@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo NecroCore Bug Tracker - Rename Dashboard
if not exist "%ROOT%tools\find_python.cmd" goto missing
if not exist "%ROOT%tools\change_name.py" goto missing
call "%ROOT%tools\find_python.cmd"
if errorlevel 1 goto failed
"%NECRO_PY%" "%ROOT%tools\change_name.py"
if errorlevel 1 goto failed
echo Dashboard name updated if shown above. Restart dashboard to apply.
pause
exit /b 0
:missing
echo ERROR: Missing package file. Extract the complete ZIP first.
:failed
echo Name change could not be completed.
pause
exit /b 1
