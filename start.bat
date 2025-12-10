@echo off
title Oracle Counter - Starting...
color 0a

echo ====================================
echo        Oracle Counter v2.0
echo        Made by Kirito
echo ====================================
echo.
echo [INFO] Checking Python installation...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo [INFO] Please install Python from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [INFO] Python found! Checking dependencies...

:: Check if required modules are installed
python -c "import tkinter, pynput" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Required modules not found. Installing...
    echo [INFO] Installing pynput...
    pip install pynput
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies!
        echo [INFO] Try running: pip install pynput
        pause
        exit /b 1
    )
)

echo [INFO] All dependencies satisfied!
echo [INFO] Starting Oracle Counter...
echo.

:: Change title and start the application
title Oracle Counter - Running
python main.py

:: Handle exit codes
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Oracle Counter exited with error code: %errorlevel%
    echo [INFO] Check the error message above for details
) else (
    echo.
    echo [INFO] Oracle Counter closed successfully!
)
echo Press any key to close this window...
pause >nul
