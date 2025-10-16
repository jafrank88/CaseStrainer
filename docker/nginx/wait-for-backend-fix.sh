#!/bin/sh
# Wait for backend to be ready before starting nginx

echo "Waiting for backend to be ready..."

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Checking backend..."
    
    # Try to resolve DNS and reach backend
    if wget -q --spider --timeout=2 http://casestrainer-backend-prod:5000/casestrainer/api/health 2>/dev/null; then
        echo "✅ Backend is ready!"
        exit 0
    fi
    
    echo "Backend not ready yet, waiting 2 seconds..."
    sleep 2
done

echo "⚠️ Backend not ready after $MAX_ATTEMPTS attempts, starting nginx anyway..."
exit 0  # Don't block nginx startup
