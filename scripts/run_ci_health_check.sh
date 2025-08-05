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

# Test analyze endpoint with realistic data
echo "Testing analyze endpoint..."
echo "Environment variables:"
echo "CI=$CI"
echo "GITHUB_ACTIONS=$GITHUB_ACTIONS"

response=$(curl -s -w "%{http_code}" -X POST http://localhost:5000/casestrainer/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "The court considered the precedent established in Miranda v. Arizona, 384 U.S. 436 (1966) regarding procedural rights. This case established important constitutional protections.", "type": "text"}')

http_code="${response: -3}"
response_body="${response%???}"

echo "Response code: $http_code"
echo "Response body: $response_body"

if [ "$http_code" = "200" ]; then
    echo "✅ Analyze endpoint is working"
else
    echo "❌ Analyze endpoint failed with code $http_code"
    echo "Response: $response_body"
    exit 1
fi

echo "✅ All health checks passed!" 