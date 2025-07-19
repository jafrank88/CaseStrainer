@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Running integration test...
cd src
python integration_test_streamlined.py quick

echo Test complete!
pause 