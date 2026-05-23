@echo off
title AI Trading Companion
color 0A

echo.
echo  ===============================================
echo   AI Trading Companion — Starting Up
echo  ===============================================
echo.

:: Check Python is available (try py launcher first, then python)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
) else (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [ERROR] Python not found. Install Python 3.10+ and add to PATH.
        pause
        exit /b 1
    )
    set PYTHON=python
)

:: Copy .env if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  [INFO] Created .env from .env.example
    )
)

echo  [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "AI Trading — Backend" cmd /k "cd /d %~dp0 && %PYTHON% -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo  [2/2] Starting Streamlit Frontend on http://localhost:8502 ...
start "AI Trading — Frontend" cmd /k "cd /d %~dp0 && %PYTHON% -m streamlit run app/main.py --server.port 8502 --server.address localhost"

timeout /t 4 /nobreak >nul

echo.
echo  ===============================================
echo   Frontend : http://localhost:8502
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/docs
echo  ===============================================
echo.
echo  Both windows are running. Close them to stop.
pause
