@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo.
echo ----------------------------------------------------------
echo NecroCore Bug Tracker - BFA C++ Bridge Installer (v53)
echo ----------------------------------------------------------
echo This changes ChatHandler.cpp and adds the NECROBUG bridge.
echo The source installer creates a backup before changing files.
echo It does NOT build or restart worldserver.
echo.

if not exist "%ROOT%tools\install_bridge.py" (
  echo ERROR: tools\install_bridge.py is missing from this folder.
  echo Install this launcher inside your Community Edition directory.
  goto failed
)
if not exist "%ROOT%server\necro_bug_addon_bridge.cpp" (
  echo ERROR: server\necro_bug_addon_bridge.cpp is missing.
  goto failed
)

rem 1. Try the interpreter recorded by 01_Setup_Dashboard.cmd.
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
if defined NECRO_PY goto run_saved

rem 2. Windows Python launcher (works without Python on PATH).
where py.exe >nul 2>nul
if not errorlevel 1 (
  py -3 --version >nul 2>nul
  if not errorlevel 1 goto run_py
)

rem 3. Ordinary Python command.
where python.exe >nul 2>nul
if not errorlevel 1 (
  python --version >nul 2>nul
  if not errorlevel 1 goto run_path
)

rem 4. Manual interpreter selection.
echo No working Python installation found automatically.
set /p "NECRO_PY=Enter the full path to python.exe: "
set "NECRO_PY=%NECRO_PY:"=%"
if not exist "%NECRO_PY%" (
  echo ERROR: Could not find python.exe at that path.
  goto failed
)
"%NECRO_PY%" --version
if errorlevel 1 goto failed
goto run_saved

:run_saved
echo Python interpreter: "%NECRO_PY%"
echo Enter the test core SOURCE root when prompted, e.g. F:\BFA-HavenCore-Test
echo.
"%NECRO_PY%" "%ROOT%tools\install_bridge.py"
goto report_status

:run_py
echo Python interpreter: py -3
echo Enter the test core SOURCE root when prompted, e.g. F:\BFA-HavenCore-Test
echo.
py -3 "%ROOT%tools\install_bridge.py"
goto report_status

:run_path
echo Python interpreter: python.exe
echo Enter the test core SOURCE root when prompted, e.g. F:\BFA-HavenCore-Test
echo.
python "%ROOT%tools\install_bridge.py"
goto report_status

:report_status
set "RC=%errorlevel%"
if not "%RC%"=="0" (
  echo.
  echo Source installer returned error code %RC%.
  goto failed
)
echo.
echo SOURCE PATCH APPLIED. No executable was built or restarted.
echo Follow docs\SERVER_INTEGRATION.md to build worldserver.
pause
exit /b 0

:failed
echo.
echo SOURCE INSTALLATION DID NOT COMPLETE. No build was triggered.
echo If an ERROR appeared above, copy it here for troubleshooting.
pause
exit /b 1
