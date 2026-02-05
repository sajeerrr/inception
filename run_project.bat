@echo off
echo Starting Inception AI Translator...
"C:\Coding Languages\python\python.exe" main.py
if %errorlevel% neq 0 (
    echo.
    echo Application crashed. See error above.
    pause
)
