@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden. Bitte Python installieren.
    pause
    exit /b 1
)

if exist "dist\MailProcessor.exe" (
    "dist\MailProcessor.exe"
) else (
    python main.py
)
if errorlevel 1 (
    echo [FEHLER] MailProcessor konnte nicht gestartet werden.
    pause
)
