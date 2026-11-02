@echo off
setlocal EnableExtensions DisableDelayedExpansion
title NecroCore Screenshot Client - Initial Setup
cd /d "%~dp0"
set "ROOT=%~dp0"
set "RUNTIME=%ROOT%runtime"
set "PY=%RUNTIME%\python.exe"
set "ZIP=%ROOT%python-3.14.3-embed-amd64.zip"
echo ==========================================================
echo NECROCORE MULTI-PC SCREENSHOT CLIENT - SETUP ON WOW PC
echo ==========================================================
echo This does not modify your server dashboard or database.
echo.
if exist "%PY%" goto run
where curl.exe >nul 2>nul
if errorlevel 1 goto download_error
where tar.exe >nul 2>nul
if errorlevel 1 goto download_error
echo Fetching portable Python from python.org (one time)...
curl.exe --fail --location --retry 2 --connect-timeout 15 --output "%ZIP%" "https://www.python.org/ftp/python/3.14.3/python-3.14.3-embed-amd64.zip"
if errorlevel 1 goto download_error
echo Verifying SHA-256...
certutil -hashfile "%ZIP%" SHA256 | findstr /I /C:"ad4961a479dedbeb7c7d113253f8db1b1935586b73c27488712beec4f2c894e6" >nul
if errorlevel 1 goto bad_checksum
if not exist "%RUNTIME%" mkdir "%RUNTIME%"
if errorlevel 1 goto fail
tar.exe -xf "%ZIP%" -C "%RUNTIME%"
if errorlevel 1 goto fail
if not exist "%PY%" goto fail
if not exist "%RUNTIME%\pythonw.exe" goto fail
del /q "%ZIP%" >nul 2>nul
:run
"%PY%" "%ROOT%necro_screenshot_client.py" --setup
if errorlevel 1 goto fail
echo.
echo SETUP COMPLETE. Run 02_Start_Hidden_On_This_PC.cmd
pause
exit /b 0
:bad_checksum
echo STOP: Runtime checksum mismatch. Not used.
del /q "%ZIP%" >nul 2>nul
goto fail
:download_error
echo STOP: Python runtime download failed. Internet needed once for setup.
:fail
echo.
echo The server dashboard and database were not changed.
pause
exit /b 1
