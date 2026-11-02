@echo off
setlocal
set "TARGET=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\NecroCore_ScreenshotClient.lnk"
if exist "%TARGET%" del "%TARGET%"
echo Removed this client's optional AutoStart entry, if it existed.
echo Existing screenshots and configuration were not touched.
pause
