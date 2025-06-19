# Let's manually create a clean nginx config to test
$nginxContent = @"
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    access_log  logs/access.log;
    error_log   logs/error.log warn;

    server {
        listen       443 ssl;
        http2 on;
        server_name  wolf.law.uw.edu localhost;
        
        ssl_certificate     "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/ssl/WolfCertBundle.crt";
        ssl_certificate_key "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/ssl/wolf.law.uw.edu.key";
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        
        client_max_body_size 100M;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        fastcgi_read_timeout 300s;

        # API routes
        location /casestrainer/api/ {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            proxy_http_version 1.1;
        }

        # Frontend routes
        location /casestrainer/ {
            alias   "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/casestrainer-vue-new/dist/";
            index   index.html;
            try_files `$uri `$uri/ /casestrainer/index.html;
        }

        location = / {
            return 301 /casestrainer/;
        }

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}
"@

# Write the config manually
$nginxContent | Out-File -FilePath "nginx.conf" -Encoding ASCII

# Test the config
& "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe" -t -c (Resolve-Path "nginx.conf").Path