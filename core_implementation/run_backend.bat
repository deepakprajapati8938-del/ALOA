@echo off
echo [ALOA] Starting Backend...
cd /d %~dp0
call .\venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Virtual environment not found! Please run setup first.
    pause
    exit /b
)
python server.py
pause
