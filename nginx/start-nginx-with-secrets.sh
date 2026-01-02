#!/bin/sh
# Start script for nginx that copies SSL key from secret to expected location

# Copy the SSL key from Docker secret to the location nginx expects
if [ -f /run/secrets/ssl_key ]; then
    echo "Copying SSL key from Docker secret..."
    cp /run/secrets/ssl_key /etc/nginx/ssl/wolf.law.uw.edu.key
    chmod 600 /etc/nginx/ssl/wolf.law.uw.edu.key
    echo "SSL key copied successfully"
else
    echo "ERROR: SSL key secret not found at /run/secrets/ssl_key"
    exit 1
fi

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration test passed, starting nginx..."
    exec nginx -g "daemon off;"
else
    echo "ERROR: nginx configuration test failed"
    exit 1
fi
