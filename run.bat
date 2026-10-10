@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11 or newer and check "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] First-time setup: creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo.
        pause
        exit /b 1
    )
    echo [INFO] Installing required packages. This may take a few minutes...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies from requirements.txt.
        echo.
        pause
        exit /b 1
    )
    echo [INFO] Setup complete.
    echo.
)

".venv\Scripts\python.exe" -m mill_motion %*
echo.
pause
endlocal
