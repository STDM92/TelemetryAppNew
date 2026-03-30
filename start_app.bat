@echo off
:: Change the working directory to the folder where this .bat file lives
cd /d "%~dp0"

:: Start the app using the venv's Python directly
.venv\scripts\python.exe dev_tools\mock_host\mock_host.py --mode live

:: If the app crashes or you close it, pause so you can read any error messages
pause