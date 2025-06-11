@echo off
setlocal enabledelayedexpansion

echo Copying Vue.js assets to deployment directory...

set "SOURCE_DIR=%~dp0casestrainer-vue-new\dist"
set "TARGET_DIR=%~dp0deployment_package\static"

if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

xcopy /E /Y /I "%SOURCE_DIR%\*" "%TARGET_DIR%"

echo Done copying Vue.js assets.
