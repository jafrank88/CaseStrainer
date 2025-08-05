#!/bin/bash

# CI Health Check Script for Linux
set -e

echo "Starting CI health checks..."

# Wait for application to be ready
echo "Waiting for application to start..."
sleep 45

# Check if the application is actually running
echo "Checking if application is running..."
if ! pgrep -f "waitress-serve" > /dev/null; then
    echo "❌ Application is not running"
    echo "Checking logs..."
    if [ -f "app.log" ]; then
        cat app.log
    fi
    exit 1
fi
echo "✅ Application process is running"

# Test basic health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:5000/casestrainer/api/health; then
    echo "✅ Health endpoint is working"
else
    echo "❌ Health endpoint failed"
    exit 1
fi

# Test main application endpoint
echo "Testing main application endpoint..."
if curl -f http://localhost:5000/casestrainer/; then
    echo "✅ Main application endpoint is working"
else
    echo "❌ Main application endpoint failed"
    exit 1
fi

# Test analyze endpoint with simple data
echo "Testing analyze endpoint..."
if curl -f -X POST http://localhost:5000/casestrainer/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test document with a citation: Roe v. Wade, 410 U.S. 113 (1973).", "type": "text"}'; then
    echo "✅ Analyze endpoint is working"
else
    echo "❌ Analyze endpoint failed"
    exit 1
fi

echo "✅ All health checks passed!" 