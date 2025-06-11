@echo off
cd /d "%~dp0"
"nginx-1.27.5\nginx.exe" -c "%~dp0nginx_local.conf"
