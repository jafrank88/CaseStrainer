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

# Test analyze endpoint with realistic data (including Roe v. Wade and Miranda v. Arizona)
echo "Testing analyze endpoint..."
echo "Environment variables:"
echo "CI=$CI"
echo "GITHUB_ACTIONS=$GITHUB_ACTIONS"

# Test with Roe v. Wade
echo "Testing with Roe v. Wade..."
response1=$(curl -s -w "%{http_code}" -X POST http://localhost:5000/casestrainer/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test document with a citation: Roe v. Wade, 410 U.S. 113 (1973).", "type": "text"}')

http_code1="${response1: -3}"
response_body1="${response1%???}"

echo "Roe v. Wade response code: $http_code1"

# Test with Miranda v. Arizona
echo "Testing with Miranda v. Arizona..."
response2=$(curl -s -w "%{http_code}" -X POST http://localhost:5000/casestrainer/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test document with a citation: Miranda v. Arizona, 384 U.S. 436 (1966).", "type": "text"}')

http_code2="${response2: -3}"
response_body2="${response2%???}"

echo "Miranda v. Arizona response code: $http_code2"

# Check both tests passed
if [ "$http_code1" = "200" ] && [ "$http_code2" = "200" ]; then
    echo "✅ Analyze endpoint is working with both Roe v. Wade and Miranda v. Arizona"
else
    echo "❌ Analyze endpoint failed"
    echo "Roe v. Wade response: $response_body1"
    echo "Miranda v. Arizona response: $response_body2"
    exit 1
fi

echo "✅ All health checks passed!" 