@echo off
echo ===================================================
echo CaseStrainer Python Path Fixer
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if D:\Python directory exists, create it if not
if not exist "D:\Python" (
    echo Creating D:\Python directory...
    mkdir "D:\Python" 2>nul
    if errorlevel 1 (
        echo Failed to create D:\Python directory. Please run as administrator.
        echo Trying an alternative approach...
    ) else (
        echo D:\Python directory created successfully.
    )
)

REM Create a temporary batch file in the current directory that will be used to start Python
echo @echo off > temp_python.bat
echo echo Starting Python from virtual environment... >> temp_python.bat
echo "%~dp0.venv\Scripts\python.exe" %* >> temp_python.bat

REM Create a symbolic link to the batch file in D:\Python if possible
if exist "D:\Python" (
    echo Creating python.exe batch file in D:\Python...
    copy temp_python.bat "D:\Python\python.exe.bat" >nul 2>&1
    if errorlevel 1 (
        echo Failed to create python.exe.bat in D:\Python.
    ) else (
        echo Created python.exe.bat in D:\Python successfully.
    )
)

REM Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 | findstr LISTENING
if "%ERRORLEVEL%"=="0" (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
) else (
    echo Port 5000 is available.
)

REM Set environment variables
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_CHEROOT=True"

REM Start the CaseStrainer Vue.js frontend using the Python executable from the virtual environment
echo Starting CaseStrainer Vue.js frontend on port 5000...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000

REM Use the Python executable from the virtual environment directly
"%~dp0.venv\Scripts\python.exe" "%~dp0app_final_vue.py" --host=0.0.0.0 --port=5000

echo.
echo CaseStrainer stopped.

REM Clean up temporary files
del temp_python.bat >nul 2>&1
