#!/bin/sh

# Create the ssl directory if it doesn't exist
mkdir -p /etc/nginx/ssl

# Create a symbolic link for the certificate
ln -sf /etc/nginx/ssl/WolfCertBundle.crt /etc/nginx/ssl/cert.pem
ln -sf /etc/nginx/ssl/wolf.law.uw.edu.key /etc/nginx/ssl/key.pem

# Start Nginx
exec nginx -g 'daemon off;'
