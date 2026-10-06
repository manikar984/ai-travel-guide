@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Install Python 3.10+ first.
        pause
        exit /b 1
    )
)

echo Installing/updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Created .env from .env.example.
    echo Open .env, add your GEMINI_API_KEY and MURF_API_KEY, then run this file again.
    pause
    exit /b 0
)

echo.
echo Starting AI Travel Guide...
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" Backend\app.py
pause
