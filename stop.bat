@echo off
echo Stopping Multi-team Knowledge Assistant services...

if exist pids.txt (
    for /f %%p in (pids.txt) do (
        taskkill /PID %%p /F >nul 2>&1
        if errorlevel 1 (
            echo   Warning: PID %%p already stopped or not found
        ) else (
            echo   OK Stopped PID %%p
        )
    )
    del pids.txt
    echo.
    echo All services stopped successfully
) else (
    echo No pids.txt found -- services may not be running or were stopped already
)

:: Also try to stop any remaining uvicorn/vite processes (fallback)
taskkill /FI "WINDOWTITLE eq uvicorn*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq vite*" /F >nul 2>&1
