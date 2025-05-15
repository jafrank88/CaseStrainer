@echo off
echo ===================================================
echo CaseStrainer Script Cleanup Utility
echo ===================================================
echo.

REM Create a directory for deprecated scripts
if not exist "deprecated_scripts" (
    echo Creating deprecated_scripts directory...
    mkdir "deprecated_scripts"
)

echo Moving unnecessary batch files to deprecated_scripts directory...

REM Scripts we created during troubleshooting
move /Y "build_vue_frontend_npm.bat" "deprecated_scripts\" 2>nul
move /Y "fix_python_path.bat" "deprecated_scripts\" 2>nul
move /Y "install_dependencies.bat" "deprecated_scripts\" 2>nul
move /Y "start_simple_vue_direct.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_direct.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_direct_venv.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_fullpath.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_system_python.bat" "deprecated_scripts\" 2>nul
move /Y "start_with_absolute_path.bat" "deprecated_scripts\" 2>nul

REM Redundant or outdated scripts
move /Y "build_vue_frontend.bat" "deprecated_scripts\" 2>nul
move /Y "build_vue_manual.bat" "deprecated_scripts\" 2>nul
move /Y "build_vue_only.bat" "deprecated_scripts\" 2>nul
move /Y "deploy_casestrainer_vue.bat" "deprecated_scripts\" 2>nul
move /Y "deploy_vue_for_nginx.bat" "deprecated_scripts\" 2>nul
move /Y "deploy_vue_frontend.bat" "deprecated_scripts\" 2>nul
move /Y "direct_run.bat" "deprecated_scripts\" 2>nul
move /Y "install_vue_dependencies.bat" "deprecated_scripts\" 2>nul
move /Y "run_casestrainer.bat" "deprecated_scripts\" 2>nul
move /Y "run_landing.bat" "deprecated_scripts\" 2>nul
move /Y "run_vue_app.bat" "deprecated_scripts\" 2>nul
move /Y "start_nginx_compatible.bat" "deprecated_scripts\" 2>nul
move /Y "start_simple.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_casestrainer.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_fixed.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_for_nginx.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_frontend.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_production.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_simple.bat" "deprecated_scripts\" 2>nul
move /Y "start_vue_simple_nginx.bat" "deprecated_scripts\" 2>nul

echo.
echo ===================================================
echo Cleanup complete!
echo ===================================================
echo.
echo The following essential scripts have been kept:
echo - start_with_d_python.bat (Main production script with correct Python path)
echo - start_for_nginx.bat (For Nginx deployment)
echo - start_casestrainer.bat (Original main startup script)
echo - build_and_deploy_vue.bat (For building Vue.js frontend)
echo - update_nginx_config.bat (For updating Nginx configuration)
echo.
echo All other batch files have been moved to the "deprecated_scripts" directory.
echo If you need any of them, you can find them there.
echo.
echo Press any key to exit...
pause > nul
