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
if exist FormatForgeWeb.spec del /q FormatForgeWeb.spec
if exist FormatForgeDesktop.spec del /q FormatForgeDesktop.spec

set "ICON_ARG="
if exist "assets\formatforge.ico" set "ICON_ARG=--icon assets\formatforge.ico"

if defined CODE_SIGN_CERT_BASE64 if defined CODE_SIGN_CERT_PASSWORD (
  echo [INFO] Firma Authenticode attiva
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\sign-executables.ps1" -Targets @("dist\FormatForgeWeb.exe","dist\FormatForgeDesktop.exe")
)

pyinstaller --noconsole --onefile --name FormatForgeWeb %ICON_ARG% --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg app.py
pyinstaller --noconsole --onefile --name FormatForgeDesktop %ICON_ARG% --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg --collect-all webview desktop_app.py

echo.
echo [DONE] EXE disponibili in dist\FormatForgeWeb.exe e dist\FormatForgeDesktop.exe
endlocal
