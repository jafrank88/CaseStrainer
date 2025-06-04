@echo off
echo Starting CaseStrainer Vue.js development server...

:: Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
  echo Installing dependencies...
  call npm install
  if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies
    exit /b %ERRORLEVEL%
  )
)

:: Start the development server
echo Starting development server...
call npm run dev

if %ERRORLEVEL% NEQ 0 (
  echo Error starting development server
  exit /b %ERRORLEVEL%
)
