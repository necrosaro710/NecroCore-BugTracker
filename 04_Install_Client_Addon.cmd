@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
echo.
echo NecroCore Bug Tracker - WoW 8.3.7 Client Addon Installer (v1.0)
echo ===============================================================
if not exist "%ROOT%client\NecroBugTracker\NecroBugTracker.lua" goto missing
if not exist "%ROOT%client\NecroBugTracker\NecroBugTracker.toc" goto missing
set "WOW="
set /p "WOW=Enter WoW TEST client folder containing Wow.exe: "
set "WOW=%WOW:"=%"
if not exist "%WOW%\Wow.exe" (
  echo ERROR: Wow.exe not found in "%WOW%". No files copied.
  goto failed
)
set "DEST=%WOW%\Interface\AddOns\NecroBugTracker"
if not exist "%WOW%\Interface\AddOns" mkdir "%WOW%\Interface\AddOns"
if errorlevel 1 goto failed
if exist "%DEST%" (
  echo Existing addon found. Back it up if needed before proceeding.
  choice /C YN /N /M "Overwrite the two addon files? [Y/N] "
  if errorlevel 2 (
    echo Cancelled. No addon files changed.
    pause
    exit /b 0
  )
) else (
  mkdir "%DEST%"
  if errorlevel 1 goto failed
)
copy /Y "%ROOT%client\NecroBugTracker\NecroBugTracker.lua" "%DEST%\NecroBugTracker.lua" >nul
if errorlevel 1 goto failed
copy /Y "%ROOT%client\NecroBugTracker\NecroBugTracker.toc" "%DEST%\NecroBugTracker.toc" >nul
if errorlevel 1 goto failed
echo ADDON INSTALLED. Restart WoW or type /reload.
pause
exit /b 0
:missing
echo ERROR: Client addon files missing. Extract the COMPLETE release ZIP first.
:failed
echo CLIENT ADDON INSTALLATION FAILED; check the message above.
pause
exit /b 1
