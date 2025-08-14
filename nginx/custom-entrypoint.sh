#!/bin/sh

# Create the conf.d directory if it doesn't exist
mkdir -p /etc/nginx/conf.d

# Copy the default configuration if it doesn't exist
if [ ! -f /etc/nginx/conf.d/default.conf ]; then
    cp /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
fi

# Start Nginx
exec nginx -g 'daemon off;'
