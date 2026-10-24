@echo off
python "%~dp0start-live-share.py" --token-env-file "%~dp0..\.env" --enable-sharing
if errorlevel 1 pause
