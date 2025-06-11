@echo off
echo Checking for processes on port 5173...
echo ================================

REM Check for any process using port 5173
echo Finding process using port 5173...
netstat -ano | findstr :5173

echo.
echo If you see a process above, you can kill it with:
echo taskkill /PID [PID] /F
echo.

echo Checking if Vite is running...
tasklist | findstr /i "node"

echo.
echo If you need to kill all Node processes, run:
echo taskkill /F /IM node.exe
echo.

pause
