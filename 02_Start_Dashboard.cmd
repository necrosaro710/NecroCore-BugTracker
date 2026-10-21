@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo.
echo NecroCore Bug Tracker - Dashboard Start (v52 launcher fix)
echo ==========================================================
echo Folder: "%ROOT%"

if not exist "%ROOT%web\launch_dashboard.py" (
  echo ERROR: web\launch_dashboard.py was not found.
  echo Run this file from inside the extracted Community Edition folder.
  goto failed
)
if not exist "%ROOT%web\config.json" (
  echo ERROR: web\config.json was not found.
  echo Run 01_Setup_Dashboard.cmd first, then run this launcher again.
  goto failed
)

rem First try the Python interpreter saved by the successful setup.
set "NECRO_PY="
if exist "%ROOT%python_path.txt" (
  for /f "usebackq delims=" %%P in ("%ROOT%python_path.txt") do (
    if not defined NECRO_PY if exist "%%~P" set "NECRO_PY=%%~P"
  )
)
if defined NECRO_PY (
  "%NECRO_PY%" --version >nul 2>nul
  if errorlevel 1 set "NECRO_PY="
)
if defined NECRO_PY goto run_interpreter

rem Fallback 1: Windows Python launcher.
where py.exe >nul 2>nul
if not errorlevel 1 (
  py -3 --version >nul 2>nul
  if not errorlevel 1 goto run_py_launcher
)

rem Fallback 2: Python executable on PATH.
where python.exe >nul 2>nul
if not errorlevel 1 (
  python --version >nul 2>nul
  if not errorlevel 1 goto run_python_path
)

rem Last resort: enter Python.exe path.
echo.
echo No working Python command found automatically.
set /p "NECRO_PY=Enter the full path to python.exe: "
set "NECRO_PY=%NECRO_PY:\"=%"
if not exist "%NECRO_PY%" (
  echo ERROR: The Python executable was not found at that location.
  goto failed
)
goto run_interpreter

:run_interpreter
echo Using Python: "%NECRO_PY%"
echo Starting dashboard... Press Ctrl+C to stop it.
echo.
"%NECRO_PY%" "%ROOT%web\launch_dashboard.py"
goto finished

:run_py_launcher
echo Using Python: py -3
echo Starting dashboard... Press Ctrl+C to stop it.
echo.
py -3 "%ROOT%web\launch_dashboard.py"
goto finished

:run_python_path
echo Using Python: python.exe (PATH)
echo Starting dashboard... Press Ctrl+C to stop it.
echo.
python "%ROOT%web\launch_dashboard.py"
goto finished

:finished
set "RC=%errorlevel%"
echo.
if not "%RC%"=="0" (
  echo Dashboard exited with code %RC%. The real error should be shown above.
  echo Copy the messages above and send them for troubleshooting.
  goto failed
)
echo Dashboard stopped.
pause
exit /b 0

:failed
echo.
echo Dashboard not started. The existing configuration and data were not changed.
pause
exit /b 1
