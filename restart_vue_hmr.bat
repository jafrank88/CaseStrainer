@echo off
echo Stopping any process on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo Killing process ID %%a...
    taskkill /F /PID %%a
)

echo Starting Vue development server with HMR...
cd /d %~dp0casestrainer-vue-new
start "" cmd /k "npm run dev"

echo Vue development server is starting with HMR enabled...
echo Please wait for the server to fully start before accessing the application.
pause
