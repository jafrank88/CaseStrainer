@echo off
set NGINX_DIR=%~dp0nginx-1.27.5
set NGINX_CONF=%~dp0nginx_local.conf

cd /d %NGINX_DIR%
start "" nginx.exe -c %NGINX_CONF%
