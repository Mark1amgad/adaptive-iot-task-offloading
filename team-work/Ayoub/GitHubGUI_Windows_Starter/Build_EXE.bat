@echo off
setlocal
cd /d "%~dp0"
echo This builds a Windows EXE using PyInstaller.
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Failed to install PyInstaller.
  pause
  exit /b 1
)
python -m PyInstaller --noconfirm --clean --onefile --windowed --name GitHubGUI github_gui.py
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo.
echo Build complete: dist\GitHubGUI.exe
pause
