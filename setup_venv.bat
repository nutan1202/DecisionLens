@echo off
echo Creating virtual environment...
python -m venv venv

echo.
echo Virtual environment created!
echo.
echo To activate it, run:
echo   venv\Scripts\activate
echo.
echo Then install dependencies:
echo   pip install -r requirements.txt
echo.
echo Then run the app:
echo   python -m uvicorn app.main:app --reload

