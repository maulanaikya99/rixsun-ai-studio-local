@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not finish. Read the message above, fix the item, and run install.cmd again.
  pause
)
