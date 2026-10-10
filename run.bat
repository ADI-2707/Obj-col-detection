@echo off
setlocal
cd /d "%~dp0"
python -m mill_motion %*
echo.
pause
endlocal
