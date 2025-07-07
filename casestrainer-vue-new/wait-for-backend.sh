#!/bin/sh

# Wait for the backend service to be resolvable
until getent hosts backend; do
  echo "Waiting for backend to be resolvable..."
  sleep 2
done

# Start Nginx
exec nginx -g 'daemon off;'
