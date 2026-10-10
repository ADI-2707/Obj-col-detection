@echo off
setlocal
cd /d "%~dp0"

python -c "import sys" >nul 2>&1
if errorlevel 1 (
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Python not detected. Installing Python via winget...
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        if not errorlevel 1 (
            echo [INFO] Python installed successfully.
            echo Please close and reopen run.bat to refresh system PATH.
            echo.
            pause
            exit /b 0
        )
    )
    echo [ERROR] Python is not installed or not in PATH.
    echo Opening https://www.python.org/downloads/ in browser...
    start https://www.python.org/downloads/
    echo Please install Python and ensure "Add python.exe to PATH" is checked.
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
