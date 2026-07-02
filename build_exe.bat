@echo off
setlocal

cd /d "%~dp0"

if not exist .venv (
  echo [INFO] Creo virtualenv .venv
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist app.spec del /q app.spec

pyinstaller --noconsole --onefile --name FormatForge --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg app.py

echo.
echo [DONE] EXE disponibile in dist\FormatForge.exe
endlocal
