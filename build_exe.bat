@echo off
cd /d "%~dp0"
echo [DBjara] Building standalone DBjara.exe...
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconsole --onefile --name DBjara app.py
echo [DBjara] Build complete! Check the 'dist' folder for DBjara.exe.
pause
