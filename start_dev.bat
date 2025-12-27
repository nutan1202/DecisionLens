@echo off
echo Starting X-Ray Dashboard...
echo.

if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload

