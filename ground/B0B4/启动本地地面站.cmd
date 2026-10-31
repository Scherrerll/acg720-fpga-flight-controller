@echo off
setlocal
chcp 65001 >nul
where py >nul 2>nul
if errorlevel 1 (
  python -X utf8 -B "%~dp0open_local.py" %*
) else (
  py -3 -X utf8 -B "%~dp0open_local.py" %*
)
set "GMFLY_LOCAL_EXIT=%ERRORLEVEL%"
if not "%GMFLY_LOCAL_EXIT%"=="0" pause
exit /b %GMFLY_LOCAL_EXIT%
