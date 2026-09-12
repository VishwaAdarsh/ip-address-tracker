@echo off
title IP PULSE — Network Intelligence Console
echo ===============================================================================
echo Starting IP PULSE — IP Intelligence, Geolocation ^& Website Risk Analysis Platform
echo ===============================================================================
echo.

if exist .venv\Scripts\python.exe (
    set PYTHON_EXEC=.venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

%PYTHON_EXEC% app.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] IP PULSE encountered an issue during execution.
    pause
)
