@echo off
echo Starting Peak Finder Pro GUI...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing GUI requirements...
pip install -r requirements_gui.txt

REM Run the GUI
echo Starting Peak Finder Pro...
python gui_main.py

pause
