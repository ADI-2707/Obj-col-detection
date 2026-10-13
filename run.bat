@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing virtual environment is invalid or from another machine.
        echo [INFO] Cleaning up invalid environment...
        rmdir /s /q .venv >nul 2>&1
    )
)

if not exist ".venv\Scripts\python.exe" (
    set "PY_CMD="

    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=python"
    )

    if not defined PY_CMD (
        py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD=py"
            set "PY_ARGS=-3"
        )
    )

    if not defined PY_CMD (
        if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
            set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
            set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        ) else if exist "C:\Program Files\Python312\python.exe" (
            set "PY_CMD=C:\Program Files\Python312\python.exe"
        ) else if exist "C:\Program Files\Python311\python.exe" (
            set "PY_CMD=C:\Program Files\Python311\python.exe"
        )
    )

    if not defined PY_CMD (
        where winget >nul 2>&1
        if not errorlevel 1 (
            echo [INFO] Python 3.11 or newer was not found.
            echo [INFO] Installing Python 3.12 via winget...
            winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
            if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
                set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
            ) else if exist "C:\Program Files\Python312\python.exe" (
                set "PY_CMD=C:\Program Files\Python312\python.exe"
            ) else (
                for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=%%B;%PATH%"
                python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
                if not errorlevel 1 set "PY_CMD=python"
            )
        )
    )

    if not defined PY_CMD (
        echo [ERROR] Python 3.11 or newer is required.
        echo Opening https://www.python.org/downloads/ in browser...
        start https://www.python.org/downloads/
        echo Please install Python 3.11 or newer and ensure "Add python.exe to PATH" is checked.
        echo.
        pause
        exit /b 1
    )

    echo [INFO] First-time setup: creating virtual environment...
    "%PY_CMD%" %PY_ARGS% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo.
        pause
        exit /b 1
    )

    echo [INFO] Installing required packages. This may take a few minutes...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
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

".venv\Scripts\python.exe" -m orbix %*
echo.
pause
endlocal
