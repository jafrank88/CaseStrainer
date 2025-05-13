Analysis Results

Not Found
# CaseStrainer Deployment Guide

This comprehensive guide provides instructions for deploying CaseStrainer to production environments, with specific focus on the current deployment at wolf.law.uw.edu/casestrainer.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- CourtListener API key (stored in config.json)
- LangSearch API key (stored in config.json)
- Docker (for the current production setup)
- Nginx (for proxying requests)

## Current System Architecture

CaseStrainer is currently deployed with the following architecture:

1. **External Access**: https://wolf.law.uw.edu/casestrainer/
2. **Nginx Proxy**: Docker container (`docker-nginx-1`) handling external requests
3. **Application Server**: Python Flask application running on port 5000

![Architecture Diagram](https://mermaid.ink/img/pako:eNptkMFqwzAMhl9F6NRCXyDdIYUNtmMPg9ELsaVmxLGDrUAp4d0nO2vXbhdJ_PrQL_0jOO8RFDTBXXvPHF2Ib4YS-8BmYHKcbGDPVhMbSYnZeepgfXx5XQbmDtZoKQxs9XDqYfPxXjfwQxGzxZDYkqOBzWKxgDNF9j6xkfKYqJJUVZJnTpSrqmZZVbOiLnNZl1LWshYyL4qyELkQRVlJWVSyqGRZybyQVSGLXMpKVLKQZS5EXuZlJYpKFKLI5b9_X_-gmVLgQMNIGVMkQ8OdDT7Qb_KUMCYa6YgpUXK0R0cDtKBHF_yZnKUWlMPgwwQqeNLRGmqhDd5Fb9vgI6gHDXfqaKTkHajgKVrqzrTHO_0CkQVwQQ)

## Docker Nginx Configuration

The application is accessible through a Docker Nginx container that handles SSL termination and proxies requests to the application server.

- **Container Name**: `docker-nginx-1`
- **Ports**: 80 (HTTP) and 443 (HTTPS)
- **Configuration File**: `/etc/nginx/conf.d/casestrainer.conf`
- **Proxy Target**: Forwards requests from `/casestrainer/` to `http://10.158.120.151:5000/`

## Application Server

The CaseStrainer application runs as a Python Flask application using Cheroot as the WSGI server.

- **Host**: 0.0.0.0 (IMPORTANT: Must listen on all interfaces, not just localhost)
- **Port**: 5000
- **Startup Command**: `python run_production.py --host 0.0.0.0 --port 5000`

## Important Notes About Current Setup

1. **Port Configuration**: The application must run on port 5000 to match the Docker Nginx configuration.

2. **Multiple Nginx Instances**: There are two Nginx installations on the system:
   - Docker Nginx container (active and handling requests)
   - Windows Nginx (should be stopped to avoid conflicts)

3. **Windows Nginx Location**: `C:\Users\jafrank\Downloads\nginx-1.27.5\nginx-1.27.5\nginx.exe`

## Installation and Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The key dependencies include:
- flask
- python-docx
- PyPDF2
- pdfminer.six
- requests
- cheroot
- eyecite

### 2. Configure API Keys

Create or update the `config.json` file in the project root:

```json
{
  "courtlistener_api_key": "your_courtlistener_api_key_here",
  "langsearch_api_key": "your_langsearch_api_key_here"
}
```

## Deployment Options

CaseStrainer can be deployed in several ways depending on your environment and requirements.

### Option 1: Current Production Setup (Docker + Windows)

This is the current setup at wolf.law.uw.edu/casestrainer.

1. **Stop any running Windows Nginx instances**:
   ```powershell
   Stop-Process -Name nginx -Force
   ```

2. **Stop any running Python instances**:
   ```powershell
   taskkill /f /im python.exe
   ```

3. **Start the CaseStrainer application on port 5000**:
   ```powershell
   cd "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
   python run_production.py --host 0.0.0.0 --port 5000
   ```
   
   > **CRITICAL**: The application must listen on all interfaces (0.0.0.0), not just localhost (127.0.0.1), so the Docker container can reach it at 10.158.120.151:5000. This is the most common cause of deployment issues - binding to 127.0.0.1 instead of 0.0.0.0 will prevent the Docker container from connecting to the application.

4. **Verify Docker Nginx is running**:
   ```powershell
   docker ps | findstr nginx
   ```

5. **Access the application**: https://wolf.law.uw.edu/casestrainer/

### Option 2: Standard Nginx Setup (Linux/Unix)

For a more traditional deployment on Linux/Unix systems:

1. Copy the provided `nginx_casestrainer.conf` to your Nginx configuration directory:
   ```bash
   sudo cp nginx_casestrainer.conf /etc/nginx/sites-available/casestrainer
   sudo ln -s /etc/nginx/sites-available/casestrainer /etc/nginx/sites-enabled/
   ```

2. Edit the configuration if needed to match your server's setup.

3. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

4. Run the application:
   ```bash
   python run_production.py --host 0.0.0.0 --port 8000
   ```
   
   > **IMPORTANT**: Always use 0.0.0.0 as the host to ensure the application is accessible from outside the local machine.

### Option 3: Development Setup

For local development:

1. Run the application in development mode:
   ```bash
   python app_final.py
   ```

2. Access the application at http://localhost:5000

## Troubleshooting

### Common Issues

1. **502 Bad Gateway Error (nginx/1.27.5)**:
   - This specific error indicates that the Nginx proxy (version 1.27.5) cannot connect to the backend application server
   - **Primary causes and solutions**:
     - **Listening interface issue**: The application MUST listen on all interfaces (0.0.0.0), not just localhost (127.0.0.1). This is the most common cause of 502 errors.
     - **Application not running**: Ensure the CaseStrainer application is running on port 5000
     - **Port mismatch**: Verify that the application is running on port 5000, which matches the Docker Nginx configuration
     - **Firewall blocking**: Check if a firewall is blocking communication between Nginx (10.158.120.151) and your application
     - **Wrong IP address**: The Docker Nginx is configured to connect to 10.158.120.151:5000 - verify this is the correct IP for your server
   - **Diagnostic steps**:
     - Check if the application is running: `tasklist | findstr python`
     - Verify the Nginx container is running: `docker ps | findstr nginx`
     - Check Nginx logs: `docker logs docker-nginx-1`
     - Check listening interfaces: `netstat -ano | findstr :5000`
     - Test local connectivity: `curl http://127.0.0.1:5000/`
     - Test external connectivity: `curl http://10.158.120.151:5000/`

2. **Application Not Starting**:
   - Check for port conflicts
   - Verify the uploads folder has proper permissions
   - Check application logs for errors

3. **File Upload Issues**:
   - Ensure the uploads folder exists and is writable
   - Check for file size limitations in Nginx configuration
   - Verify that the application has proper error handling for file uploads

4. **API Key Issues**:
   - Verify that `config.json` exists and contains valid API keys
   - Check application logs for API authentication errors

## Configuration Files

### Docker Nginx Configuration

Location: `/etc/nginx/conf.d/casestrainer.conf` in the Docker container

```nginx
# CaseStrainer configuration
server {
    listen 443 ssl;
    server_name wolf.law.uw.edu;

    # SSL configuration
    ssl_certificate /etc/ssl/WolfCertBundle.crt;
    ssl_certificate_key /etc/ssl/wolf.law.uw.edu.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # CaseStrainer application
    location /casestrainer/ {
        proxy_pass http://10.158.120.151:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for SSE
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
    }
}
```

### Application Configuration

The application configuration is managed through `run_production.py`, which starts the Flask application with Cheroot.

## Maintenance and Updates

### Updating the Application

1. Pull the latest changes from the repository:
   ```bash
   git pull origin main
   ```

2. Install any new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Restart the application following the deployment steps above.

### Monitoring

Monitor the application logs for errors and performance issues:

- Application logs are output to the console
- Nginx logs can be viewed with `docker logs docker-nginx-1`

## Security Considerations

1. **API Keys**: Store API keys securely in `config.json` and ensure this file is not committed to version control.

2. **SSL/TLS**: The current setup uses SSL/TLS for secure communication. Ensure certificates are kept up to date.

3. **File Uploads**: The application validates file types and implements proper error handling for file uploads.

## Contact and Support

For issues or questions about the deployment, contact the system administrator or refer to the project documentation.
