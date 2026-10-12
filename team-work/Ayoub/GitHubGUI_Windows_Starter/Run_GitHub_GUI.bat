@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
python github_gui.py
if errorlevel 1 pause
