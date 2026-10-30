@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
set "RUNTIME=%ROOT%client_helper\runtime"
set "PY=%RUNTIME%\python.exe"
set "ZIP=%ROOT%client_helper\python-3.14.3-embed-amd64.zip"
echo NecroCore Screenshot Companion v1.2 - WOW CLIENT PC ONLY
echo ----------------------------------------------------------
echo Runs using a private portable Python runtime; no Windows Python installation needed.
if not exist "%ROOT%client_helper\necro_screenshot_companion.py" goto missing
if exist "%PY%" goto launch
echo.
echo Downloading official 64-bit portable Python from python.org (one time, about 12 MB)...
where curl.exe >nul 2>nul
if errorlevel 1 goto download_error
curl.exe --fail --location --retry 2 --connect-timeout 15 --output "%ZIP%" "https://www.python.org/ftp/python/3.14.3/python-3.14.3-embed-amd64.zip"
if errorlevel 1 goto download_error
echo Checking SHA-256 integrity against the official Python release manifest...
certutil -hashfile "%ZIP%" SHA256 | findstr /I /C:"ad4961a479dedbeb7c7d113253f8db1b1935586b73c27488712beec4f2c894e6" >nul
if errorlevel 1 goto bad_checksum
if not exist "%RUNTIME%" mkdir "%RUNTIME%"
if errorlevel 1 goto failed
tar.exe -xf "%ZIP%" -C "%RUNTIME%"
if errorlevel 1 goto failed
if not exist "%PY%" goto failed
del /q "%ZIP%" >nul 2>nul
:launch
"%PY%" "%ROOT%client_helper\necro_screenshot_companion.py"
if errorlevel 1 goto failed
pause
exit /b 0
:bad_checksum
echo ERROR: Download did not match the official SHA-256. Refusing to run it.
del /q "%ZIP%" >nul 2>nul
goto failed
:download_error
echo ERROR: The portable runtime could not download. Internet required one time.
echo This PC was NOT modified. Try again online, or install Python 3.9+ separately.
goto failed
:missing
echo ERROR: Extract the entire v1.2 ZIP before running this CMD.
:failed
pause
exit /b 1
