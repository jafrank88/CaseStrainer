#!/bin/sh

# Start Nginx directly since backend should be running
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
