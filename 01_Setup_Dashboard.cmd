@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo.
echo NecroCore Bug Tracker - Community Dashboard Setup (v1.0)
echo ==========================================================
echo Package folder: "%ROOT%"
echo.

rem Do not rely on the current working directory or a successful CD.
rem When a CMD is launched directly inside a ZIP, Explorer may unpack only this CMD.
if not exist "%ROOT%tools\find_python.cmd" goto missing
if not exist "%ROOT%tools\setup.py" goto missing
if not exist "%ROOT%web\dashboard.py" goto missing
if not exist "%ROOT%web\launch_dashboard.py" goto missing

call "%ROOT%tools\find_python.cmd"
if errorlevel 1 (
  echo ERROR: Could not find or start a working Python interpreter.
  goto failed
)
if not defined NECRO_PY (
  echo ERROR: Python detection did not return an executable path.
  goto failed
)
echo.
echo Python: "%NECRO_PY%"
echo Starting dashboard setup...
echo.
"%NECRO_PY%" "%ROOT%tools\setup.py"
if errorlevel 1 (
  echo ERROR: Dashboard setup returned a nonzero exit code.
  goto failed
)
echo.
echo DASHBOARD SETUP COMPLETED.
echo Next run 02_Start_Dashboard.cmd from this same extracted folder.
pause
exit /b 0

:missing
echo ERROR: The complete Community Edition package was not found.
echo Missing file(s) next to this installer:
if not exist "%ROOT%tools\find_python.cmd" echo   tools\find_python.cmd
if not exist "%ROOT%tools\setup.py" echo   tools\setup.py
if not exist "%ROOT%web\dashboard.py" echo   web\dashboard.py
if not exist "%ROOT%web\launch_dashboard.py" echo   web\launch_dashboard.py
echo.
echo Do NOT run the CMD inside the ZIP or copy the CMD by itself.
echo Right-click the release ZIP, choose Extract All, then open its
 echo extracted NecroCore_Bug_Tracker_Community_Edition folder and run
 echo 01_Setup_Dashboard.cmd there.
goto failed

:failed
echo.
echo SETUP FAILED. No core/database/build changes were requested.
pause
exit /b 1
