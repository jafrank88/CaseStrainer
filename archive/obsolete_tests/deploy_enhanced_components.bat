@echo off
echo ===================================================
echo CaseStrainer Enhanced Components Deployment Script
echo ===================================================
echo.

REM Create backup of original components
echo Creating backup of original components...
cd /d "%~dp0"
if not exist "backup\components" mkdir "backup\components"
if exist "static\vue\js\components\FileUpload.js" copy "static\vue\js\components\FileUpload.js" "backup\components\FileUpload.js.bak"
if exist "static\vue\js\components\TextPaste.js" copy "static\vue\js\components\TextPaste.js" "backup\components\TextPaste.js.bak"
echo Backup created.

REM Copy the enhanced components to the static directory
echo Copying enhanced components to the static directory...
xcopy /Y "casestrainer-vue\src\components\EnhancedFileUpload.vue" "static\vue\components\"
xcopy /Y "casestrainer-vue\src\components\EnhancedTextPaste.vue" "static\vue\components\"
echo Enhanced components copied.

REM Update the Home.vue component in the static directory
echo Updating Home.vue in the static directory...
xcopy /Y "casestrainer-vue\src\views\Home.vue" "static\vue\views\"
echo Home.vue updated.

echo.
echo Enhanced components have been deployed to the static directory.
echo.
echo Now restarting the server to apply changes...
echo.

REM Restart the server
call "%~dp0\start_for_nginx.bat"

echo.
echo Deployment complete. Please access the application at:
echo - Local URL: http://127.0.0.1:5000
echo - Production URL: https://wolf.law.uw.edu/casestrainer/
echo.
