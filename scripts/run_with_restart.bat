@echo off
title CaseStrainer Auto-Restart Script

:start
  echo [%date% %time%] Starting CaseStrainer application...
  python -m src.app_final_vue
  
  echo [%date% %time%] Application exited with code %errorlevel%
  
  set /a "count=0"
  :wait
    timeout /t 5 /nobreak >nul
    set /a "count+=1"
    if %count% gtr 10 (
      echo [%date% %time%] Restart limit reached. Please check the application logs.
      pause
      exit /b 1
    )
    
    echo [%date% %time%] Restarting in 5 seconds... (Press Ctrl+C to cancel)
    
  goto :wait

goto :start
