@echo off
echo Building CaseStrainer Vue.js application...

:: Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
  echo Installing dependencies...
  call npm install
  if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies
    exit /b %ERRORLEVEL%
  )
)

:: Build the application for production
echo Building application...
call npm run build
if %ERRORLEVEL% NEQ 0 (
  echo Error building application
  exit /b %ERRORLEVEL%
)

echo Build completed successfully!
echo The built files are in the 'dist' directory.
