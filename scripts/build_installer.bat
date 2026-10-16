@echo off
setlocal
cd /d "%~dp0\.."

call scripts\build_exe.bat
if errorlevel 1 (
    echo [ERROR] Build executable step failed.
    exit /b 1
)

set "ISCC_EXE="

where iscc >nul 2>&1
if not errorlevel 1 (
    set "ISCC_EXE=iscc"
)

if not defined ISCC_EXE (
    if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
        set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    ) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
        set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
        set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    )
)

if not defined ISCC_EXE (
    echo [WARN] Inno Setup compiler (ISCC.exe) was not found.
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Installing Inno Setup via winget...
        winget install JRSoftware.InnoSetup --accept-package-agreements --accept-source-agreements
        if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
            set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
        ) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
            set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
        )
    )
)

if not defined ISCC_EXE (
    echo [ERROR] Inno Setup is required to compile the Windows installer.
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    exit /b 1
)

echo [INFO] Compiling installer with Inno Setup...
"%ISCC_EXE%" installer\VisionSetup.iss
if errorlevel 1 (
    echo [ERROR] Installer compilation failed.
    exit /b 1
)

echo [INFO] Setup installer successfully created in dist\
endlocal
