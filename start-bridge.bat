@echo off
REM Bridge M0 one-click start — double-click this file. Keep window open.
cd /d "%~dp0backend"
echo Bridge starting — keep this window open.
echo PC:   http://127.0.0.1:8000/
echo Phone (same Wi-Fi): see the Phone URL printed below.
python -m uvicorn app:app --host 0.0.0.0 --port 8000
echo.
echo Backend stopped. Press any key to close.
pause >nul
