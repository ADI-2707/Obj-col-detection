@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found. Run run.bat first to initialize.
    exit /b 1
)

echo [INFO] Checking build dependencies...
".venv\Scripts\python.exe" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller into .venv...
    ".venv\Scripts\python.exe" -m pip install "pyinstaller>=6.5"
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)

echo [INFO] Building standalone executable bundle via PyInstaller...
".venv\Scripts\python.exe" -m PyInstaller packaging\vision.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

if not exist "dist\Vision\Vision.exe" (
    echo [ERROR] Application executable was not created in dist\.
    exit /b 1
)

echo [INFO] Standalone application bundle successfully created in dist\
endlocal
