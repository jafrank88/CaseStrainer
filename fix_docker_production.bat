@echo off
echo 🔧 Fixing Docker Production Services
echo ==================================================

echo.
echo 📋 Step 1: Stopping all services...
docker-compose -f docker-compose.prod.yml down

echo.
echo 📋 Step 2: Stopping Flask development server...
echo Looking for processes using port 5000...
netstat -ano | findstr :5000
if %errorlevel% equ 0 (
    echo Found process using port 5000
    echo Killing Python processes...
    taskkill /F /IM python.exe
) else (
    echo No process found using port 5000
)

echo.
echo 📋 Step 3: Cleaning up Docker resources...
docker container prune -f
docker network prune -f

echo.
echo 📋 Step 4: Starting Redis...
docker-compose -f docker-compose.prod.yml up -d redis

echo Waiting for Redis to be ready...
timeout /t 10 /nobreak >nul

echo.
echo 📋 Checking Redis status...
docker-compose -f docker-compose.prod.yml logs redis

echo.
echo 📋 Step 5: Starting backend...
docker-compose -f docker-compose.prod.yml up -d backend

echo Waiting for backend to be ready...
timeout /t 15 /nobreak >nul

echo.
echo 📋 Checking backend status...
docker-compose -f docker-compose.prod.yml logs backend

echo.
echo 📋 Step 6: Starting all services...
docker-compose -f docker-compose.prod.yml up -d

echo.
echo 📋 Step 7: Checking final status...
docker-compose -f docker-compose.prod.yml ps

echo.
echo ✅ Docker production services fix completed!
echo.
echo 🌐 Services should be available at:
echo    Backend API: http://localhost:5001
echo    Frontend: http://localhost:8080
echo    Nginx: http://localhost:80

echo.
pause 