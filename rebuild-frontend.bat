@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0rebuild-frontend.ps1" %*
