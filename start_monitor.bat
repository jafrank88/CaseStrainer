@echo off
echo Starting CaseStrainer Health Monitor...
echo Press Ctrl+C to stop

REM Change to the script directory
cd /d "%~dp0"

REM Run the monitor in continuous mode
python monitor_health.py --config config.json --continuous

pause 