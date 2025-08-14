$content = @'
server {
    listen 80;
    server_name localhost;
    
    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Handle the root path with a redirect to /casestrainer/
    location = / {
        return 301 /casestrainer/;
    }

    # API proxy to backend
    location ^~ /casestrainer/api/ {
        proxy_pass http://casestrainer-backend-prod:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host `$host;
        proxy_cache_bypass `$http_upgrade;
        proxy_redirect off;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        send_timeout 300s;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With" always;
        
        # Handle preflight requests
        if (`$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With" always;
            add_header Content-Type "text/plain";
            add_header Content-Length 0;
            return 204;
        }
    }

    # Serve static files directly with proper caching
    # Exclude API paths from static file matching
    location ~* ^/casestrainer/(?!api/)(.*\.(?:js|css|png|jpg|jpeg|gif|ico|woff|woff2|ttf|svg|eot))$ {
        alias /usr/share/nginx/html/casestrainer/`$1;
        access_log off;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    # Handle the /casestrainer/ path
    location ^~ /casestrainer/ {
        # Remove the /casestrainer prefix for file lookup
        alias /usr/share/nginx/html/casestrainer/;
        
        # Try to serve the file directly, fall back to index.html for SPA routing
        try_files `$uri `$uri/ /casestrainer/index.html;
        
        # Add headers for single page app
        add_header Cache-Control 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0';
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }

    # Handle 404 errors
    error_page 404 /index.html;
    
    # Disable logging for favicon.ico
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    # Security headers for all responses
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
'@

Set-Content -Path "nginx.conf" -Value $content -Encoding UTF8
