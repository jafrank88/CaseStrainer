#!/bin/bash
# Worker restart script for CaseTrainer
# This script monitors the RQ worker and restarts it if it dies

set -e

WORKER_CONTAINER="casestrainer-rqworker"
MAX_RESTARTS=10
RESTART_COUNT=0

echo "Starting worker monitor script..."

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "Starting RQ worker (attempt $((RESTART_COUNT + 1))/$MAX_RESTARTS)"
    
    # Start the worker
    docker-compose up -d rqworker
    
    # Wait a moment for the worker to start
    sleep 5
    
    # Monitor the worker
    while true; do
        # Check if the worker container is running
        if ! docker ps --format "table {{.Names}}" | grep -q "^${WORKER_CONTAINER}$"; then
            echo "Worker container is not running, restarting..."
            break
        fi
        
        # Check if the worker process is healthy
        if ! docker exec $WORKER_CONTAINER python -c "import redis; r = redis.Redis(host='redis', port=6379); r.ping()" 2>/dev/null; then
            echo "Worker health check failed, restarting..."
            break
        fi
        
        # Wait before next check
        sleep 30
    done
    
    # Stop the worker gracefully
    echo "Stopping worker gracefully..."
    docker-compose stop rqworker
    
    # Wait a moment before restarting
    sleep 10
    
    RESTART_COUNT=$((RESTART_COUNT + 1))
done

echo "Maximum restart attempts reached. Worker monitor stopping."
exit 1 