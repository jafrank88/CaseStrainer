@echo off
echo === Debugging Vue.js Development Server ===
echo.

echo 1. Checking network connections on port 5173...
echo ===========================================
netstat -ano | findstr :5173

echo.
echo 2. Checking for Node.js processes...
echo ===============================
tasklist | findstr /i "node"

echo.
echo 3. Checking if port 5173 is accessible locally...
echo =========================================
powershell -command "Test-NetConnection -ComputerName localhost -Port 5173"

echo.
echo 4. Checking firewall settings...
echo =======================
netsh advfirewall firewall show rule name=all | findstr /i "5173"

echo.
echo 5. Checking hosts file for any custom localhost entries...
echo =============================================
type %SystemRoot%\System32\drivers\etc\hosts | findstr /i "localhost"

echo.
echo 6. Trying to access the server via PowerShell...
echo =================================
powershell -command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 5; 'Server responded with status code: ' + $response.StatusCode } catch { 'Error: ' + $_.Exception.Message }"

echo.
echo === Debug Information Complete ===
pause
