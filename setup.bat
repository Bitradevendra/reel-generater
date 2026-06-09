@echo off
echo ============================================================
echo   REEL GENERATOR - Environment Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+ first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo.
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip -q

echo.
echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo To run the Reel Generator:
echo   1. Activate: venv\Scripts\activate
echo   2. Run:      python main.py
echo.
echo Prerequisites:
echo   - model.gguf in script/ folder (DeepSeek R1)
echo   - Google Chrome installed (for image scraping)
echo   - ffmpeg installed and in PATH (for video encoding)
echo.
pause
