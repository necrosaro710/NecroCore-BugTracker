@echo off
rem Community Edition Python interpreter detection, v53.
rem Called via CALL from 01_Setup_Dashboard.cmd and 05_Change_Dashboard_Name.cmd.
set "NECRO_PY="
if exist "%~dp0..\python_path.txt" (
  for /f "usebackq delims=" %%P in ("%~dp0..\python_path.txt") do (
    if not defined NECRO_PY if exist "%%~P" set "NECRO_PY=%%~P"
  )
)
if defined NECRO_PY goto validate

rem Locate a real interpreter instead of saving py.exe, which may need -3 arguments.
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined NECRO_PY set "NECRO_PY=%%P"
if defined NECRO_PY goto validate
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do if not defined NECRO_PY set "NECRO_PY=%%P"
if defined NECRO_PY goto validate

echo Python not found automatically.
set /p "NECRO_PY=Enter the full path to python.exe: "
set "NECRO_PY=%NECRO_PY:"=%"

:validate
if not defined NECRO_PY exit /b 1
if not exist "%NECRO_PY%" (
  echo ERROR: Python executable path does not exist.
  exit /b 1
)
"%NECRO_PY%" --version
if errorlevel 1 (
  echo ERROR: Python executable could not be started.
  exit /b 1
)
exit /b 0
