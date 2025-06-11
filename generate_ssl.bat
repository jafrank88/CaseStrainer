@echo off
setlocal

set OPENSSL_PATH=openssl
set SSL_DIR=nginx-1.27.5\conf\ssl

if not exist "%SSL_DIR%" (
    mkdir "%SSL_DIR%"
)

echo Generating self-signed SSL certificate...

%OPENSSL_PATH% req -x509 -nodes -days 365 -newkey rsa:2048 ^
    -keyout "%SSL_DIR%\key.pem" ^
    -out "%SSL_DIR%\cert.pem" ^
    -subj "/CN=localhost" ^
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo Failed to generate SSL certificate. Make sure OpenSSL is installed and in your PATH.
    echo You can download OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html
    exit /b 1
)

echo SSL certificate generated successfully in %SSL_DIR%\

endlocal
