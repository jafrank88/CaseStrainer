@echo off
echo Building and running Hyperscan in Docker...

:: Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

:: Build and run the container
docker-compose -f docker-compose.hyperscan.yml up --build

echo Done! 