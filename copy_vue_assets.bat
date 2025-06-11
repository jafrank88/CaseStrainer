@echo off
setlocal enabledelayedexpansion

set "SOURCE_DIR=%~dp0casestrainer-vue-new\dist"
set "TARGET_DIR=%~dp0deployment_package\static"

echo Copying Vue.js assets from %SOURCE_DIR% to %TARGET_DIR%

if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

xcopy /E /Y /I "%SOURCE_DIR%\*" "%TARGET_DIR%"

echo Done copying Vue.js assets.
