GitHub GUI - Adaptive IoT (Windows)

Files:
- github_gui.py: application source
- Run_GitHub_GUI.bat: run without building an EXE
- Build_EXE.bat: install PyInstaller and build dist\GitHubGUI.exe

Requirements:
1. Install Git for Windows and make sure `git --version` works in Command Prompt.
2. Install Python 3 from https://www.python.org/downloads/windows/
   Enable "Add Python to PATH" in the installer.
3. Double-click Run_GitHub_GUI.bat to test the app.
4. To build the EXE, double-click Build_EXE.bat and wait for it to finish.
   The EXE will be in the dist folder.

The app defaults to:
D:\computer network research\adaptive-iot-task-offloading

It uses the existing local repository. It does not clone or download the project again.

Safety:
- Pull is blocked if the working tree has changes.
- Commit only includes staged files and asks before committing staged files outside
  team-work/Ayoub/rl_model/.
- Push asks for confirmation.
- Merge conflicts must be resolved manually.
