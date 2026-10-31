@echo off
setlocal
chcp 65001 >nul
where py >nul 2>nul
if errorlevel 1 (
  python -X utf8 -B "%~dp0local\open_console.py" %*
) else (
  py -3 -X utf8 -B "%~dp0local\open_console.py" %*
)
set "GMFLY_OPEN_EXIT=%ERRORLEVEL%"
if not "%GMFLY_OPEN_EXIT%"=="0" pause
exit /b %GMFLY_OPEN_EXIT%
