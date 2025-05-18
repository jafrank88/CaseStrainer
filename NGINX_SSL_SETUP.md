# CaseStrainer Nginx SSL Configuration Guide

This document provides comprehensive instructions for configuring Nginx with SSL for the CaseStrainer application.

## Overview

CaseStrainer uses a Windows Nginx installation (not Docker) to handle SSL termination and proxy requests to the Flask application running on port 5000.

## Configuration Details

### Nginx Location
- Windows Nginx is installed at: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5`
- Configuration file: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\conf\nginx.conf`
- Log files: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\logs\`

### SSL Certificates
- Certificate bundle: `D:/CaseStrainer/ssl/WolfCertBundle.crt`
- Private key: `D:/CaseStrainer/ssl/wolf.law.uw.edu.key`

### Key Configuration Elements

1. **HTTP Server Block (Redirect to HTTPS)**
```nginx
# HTTP server - redirect to HTTPS for domain
server {
    listen 80;
    server_name wolf.law.uw.edu 128.208.154.3;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://$host$request_uri;
}
```

2. **HTTP Server Block (Local Testing)**
```nginx
# HTTP server for local testing
server {
    listen 80;
    server_name localhost 127.0.0.1;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # CaseStrainer Application
    location /casestrainer/ {
        # Proxy settings
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /casestrainer;
    }
}
```

3. **HTTPS Server Block**
```nginx
# HTTPS server
server {
    listen 443 ssl;
    http2 on;
    server_name wolf.law.uw.edu localhost 127.0.0.1 128.208.154.3;

    # SSL configuration
    ssl_certificate D:/CaseStrainer/ssl/WolfCertBundle.crt;
    ssl_certificate_key D:/CaseStrainer/ssl/wolf.law.uw.edu.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # CaseStrainer Application
    location /casestrainer/ {
        # Proxy settings
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /casestrainer;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
}
```

## Critical Configuration Details

1. **Proxy Pass Configuration**
   - Do NOT include a trailing slash in the proxy_pass directive
   - Correct: `proxy_pass http://localhost:5000;`
   - Incorrect: `proxy_pass http://localhost:5000/;`

2. **URL Prefix Handling**
   - Always include the X-Forwarded-Prefix header: `proxy_set_header X-Forwarded-Prefix /casestrainer;`
   - This ensures the Flask application correctly handles the URL prefix

3. **Server Name Configuration**
   - Include all possible hostnames: `server_name wolf.law.uw.edu localhost 127.0.0.1 128.208.154.3;`

## Starting and Stopping Nginx

### Stop Nginx
```powershell
taskkill /F /IM nginx.exe
```

### Start Nginx
```powershell
Start-Process -FilePath "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe" -NoNewWindow
```

### Test Nginx Configuration
```powershell
cd "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5"
.\nginx.exe -t
```

## Starting the CaseStrainer Application

Use the `start_for_nginx.bat` script to start the CaseStrainer application:
```powershell
.\scripts\start_for_nginx.bat
```

This script:
1. Stops any running Windows Nginx instances
2. Checks if port 5000 is available and stops any conflicting processes
3. Starts the CaseStrainer application with the correct host (0.0.0.0) and port (5000) settings

## Accessing the Application

- External access: https://wolf.law.uw.edu/casestrainer/
- Local access: http://localhost/casestrainer/

## Troubleshooting

### 502 Bad Gateway
- Check that the Flask application is running on port 5000
- Verify with: `netstat -ano | findstr :5000`

### 405 Method Not Allowed
- Check the proxy_pass configuration and URL prefix handling
- Ensure the X-Forwarded-Prefix header is set correctly

### Redirection Loops
- Remove trailing slashes from proxy_pass directives
- Check the Flask application's URL prefix handling

### SSL Certificate Issues
- Verify the certificate files exist at the specified paths
- Check the certificate expiration dates

### Checking Logs
- Nginx error logs: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\logs\casestrainer_error.log`
- Nginx access logs: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\logs\casestrainer_access.log`
- Flask application logs: `C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\logs\casestrainer.log`
