@echo off
setlocal
cd /d "%~dp0"

set "ZIP_NAME=Vision.zip"

if exist "%ZIP_NAME%" del /f /q "%ZIP_NAME%"

where tar >nul 2>&1
if not errorlevel 1 (
    tar -a -c -f "%ZIP_NAME%" --exclude=".venv" --exclude="venv" --exclude="env" --exclude=".git" --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".vscode" --exclude=".idea" --exclude="*.zip" --exclude="*.log" --exclude="data/logs/*.csv" --exclude="data\logs\*.csv" LICENSE README.md requirements.txt pyproject.toml run.bat package.bat yolov8n.pt assets data vision scripts tests
) else (
    powershell -NoProfile -Command "$dest = '%ZIP_NAME%'; if (Test-Path $dest) { Remove-Item -Force $dest }; $files = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\(\.venv|venv|env|\.git|__pycache__|\.pytest_cache|\.vscode|\.idea)(\\|$)' -and $_.Name -notmatch '\.(zip|log|pyc)$' -and -not ($_.FullName -match 'data\\logs\\.*\.csv$') }; Compress-Archive -Path $files.FullName -DestinationPath $dest -Force"
)

if exist "%ZIP_NAME%" (
    echo [INFO] Successfully created %ZIP_NAME%
    for %%F in ("%ZIP_NAME%") do echo [INFO] Size: %%~zF bytes
) else (
    echo [ERROR] Failed to create %ZIP_NAME%
    exit /b 1
)

endlocal
