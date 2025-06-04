# CaseStrainer Deployment Guide

---
## Quick Start for New Contributors

- **Use `commit_push_and_deploy.bat` for standard deployments** - Handles git operations and starts the application
- **Use `start_casestrainer.bat` for development/restarts** - Just starts the application
- **Build the Vue.js frontend with `build_and_deploy_vue.bat`** - Only needed for frontend changes
- **All API endpoints use `/casestrainer/api/` prefix** - Configured in Nginx and Flask
- **Copy `.env.example` to `.env` and fill in your secrets** - Never commit real secrets!
- **Install pre-commit hooks** for code quality:
  ```bash
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```
- **Check logs in the `logs/` directory** if issues arise
- **Nginx logs** are in `nginx-1.27.5/logs/`

---

This document provides comprehensive instructions for deploying and maintaining the CaseStrainer application with its Vue.js frontend.

## Deployment Architecture

CaseStrainer uses a multi-tier architecture:

1. **Frontend**: Vue.js application served by Flask
2. **Backend**: Flask application with RESTful API endpoints
3. **Proxy**: Windows Nginx (v1.27.5) for external HTTPS access
4. **Database**: SQLite database for citation storage
5. **SSL/TLS**: Managed by Nginx with Let's Encrypt certificates

### Access Points
- **Main Application**: https://wolf.law.uw.edu/casestrainer/
- **API Endpoint**: https://wolf.law.uw.edu/casestrainer/api/analyze (proxied to http://localhost:5000/api/analyze)
- **Local Development**: http://localhost:5000/
  - Local API: http://localhost:5000/api/...

## System Requirements

- **Python 3.8+** with pip
- **Windows Nginx 1.27.5** (included in repository)
- **Node.js 16+** and npm (for frontend development only)
- **Port 5000** must be available for the Flask application
- **Ports 80/443** must be available for Nginx
- **SSL Certificates** must be installed at `D:/CaseStrainer/ssl/`:
  - `WolfCertBundle.crt`
  - `wolf.law.uw.edu.key`
- **Windows** environment with PowerShell 5.1+

## Deployment Steps

## Deployment Methods

### 1. Standard Deployment (Development)

For local development without Nginx:

```powershell
.\start_casestrainer.bat
```

This will:
- Stop any running Python processes on port 5000
- Install/update Python dependencies
- Start the Flask development server on http://localhost:5000/

### 2. Production Deployment with Nginx

For production deployment with HTTPS:

1. Run the deployment script:
   ```powershell
   .\commit_push_and_deploy.bat
   ```
   
   This will:
   - Commit and push changes to git
   - Stop any running Nginx instances
   - Start the Flask application on port 5000
   - Start Nginx with the proper configuration

2. Verify the deployment:
   - Access the application at https://wolf.law.uw.edu/casestrainer/
   - Check Nginx logs at `nginx-1.27.5/logs/casestrainer_error.log`
   - Check application logs in the `logs/` directory

### 3. Manual Nginx Management

To manually manage Nginx:

```powershell
# Stop Nginx
taskkill /F /IM nginx.exe

# Start Nginx (from project root)
Start-Process -FilePath ".\nginx-1.27.5\nginx.exe" -NoNewWindow

# Check if Nginx is running
tasklist | findstr nginx
```

## Access URLs

- **External access** (through Nginx proxy): https://wolf.law.uw.edu/casestrainer/
- **Local access** (direct): http://127.0.0.1:5000/

## Frontend Deployment

See `docs/DEPLOYMENT_VUE.md` for instructions on building and deploying the Vue.js frontend.

## Troubleshooting
- If you see a 502 Bad Gateway error, check that the Flask application is running on port 5000 and Nginx is properly configured.
- If you see path or 404 errors, ensure the Nginx proxy and frontend are using the `/casestrainer` prefix and API endpoints are under `/casestrainer/api/`.

## API Configuration

### Base Path
All API endpoints use the `/casestrainer/api/` prefix. Example endpoints:

- **File Analysis**: `POST /casestrainer/api/analyze`
- **Text Analysis**: `POST /casestrainer/api/analyze`
- **URL Analysis**: `POST /casestrainer/api/analyze`

### Important Notes
1. **Frontend Configuration**:
   - Must use absolute paths with the `/casestrainer` prefix
   - API requests should be made to `/casestrainer/api/*`

2. **Backend Configuration**:
   - Flask routes are registered with the `/api` prefix in `app_final_vue.py`
   - Nginx handles the `/casestrainer` prefix

3. **Troubleshooting**:
   - 404 errors: Check path prefixes in both frontend and backend
   - 405 Method Not Allowed: Verify the HTTP method matches the endpoint
   - 502 Bad Gateway: Ensure Flask is running on port 5000

### Startup Script

Always use `start_casestrainer.bat` to start or restart the application. All other batch files are archived and unsupported.
- For SSL/HTTPS issues, verify your Nginx SSL configuration matches the documented paths and certificates.

## Configuration Files

### 1. Application Configuration

The application uses a `config.json` file in the project root for configuration:

```json
{
  "COURTLISTENER_API_KEY": "your-api-key-here",
  "SECRET_KEY": "your-secret-key-here"
}
```

## Nginx Configuration

The Windows Nginx server handles HTTPS termination and reverse proxying. Key configuration:

### Main Configuration (`nginx-1.27.5/conf/nginx.conf`)

```nginx
# HTTPS server
server {
    listen 443 ssl http2;
    server_name wolf.law.uw.edu localhost 127.0.0.1 128.208.154.3;

    # SSL configuration
    ssl_certificate D:/CaseStrainer/ssl/WolfCertBundle.crt;
    ssl_certificate_key D:/CaseStrainer/ssl/wolf.law.uw.edu.key;
    
    # Proxy configuration for /casestrainer/
    location /casestrainer/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-Prefix /casestrainer;
        # ... other proxy settings ...
    }
}
```

### Key Settings
- **SSL Certificates**: Located at `D:/CaseStrainer/ssl/`
- **Proxy Target**: `http://127.0.0.1:5000`
- **URL Prefix**: `/casestrainer`
- **Headers**: `X-Forwarded-Prefix` is set for proper URL generation

### Important Notes
1. **No Trailing Slash**: The `proxy_pass` directive should NOT have a trailing slash
2. **Required Headers**: `X-Forwarded-Prefix` is essential for proper URL generation
3. **Hostnames**: All possible hostnames are included in `server_name`

## Troubleshooting

### Common Issues

#### 1. 502 Bad Gateway
- **Cause**: Flask application not running or not accessible on port 5000
- **Solution**:
  ```powershell
  # Check if Flask is running
  netstat -ano | findstr :5000
  
  # If not, start it manually
  python src/app_final_vue.py --host=0.0.0.0 --port=5000
  ```

#### 2. 404 Not Found
- **Cause**: Incorrect URL path or Nginx configuration
- **Solution**:
  - Verify the URL includes `/casestrainer/` prefix
  - Check Nginx configuration for proper `proxy_pass` settings
  - Ensure Flask routes are correctly prefixed with `/api`

#### 3. 405 Method Not Allowed
- **Cause**: Incorrect HTTP method used for the endpoint
- **Solution**:
  - Check the API documentation for the correct HTTP method
  - Verify the endpoint URL is correct

### Log Files

1. **Nginx Error Log**:
   ```
   nginx-1.27.5/logs/casestrainer_error.log
   ```

2. **Application Logs**:
   ```
   logs/casestrainer.log
   ```

3. **Windows Event Log**:
   - Check for system-level errors related to Nginx or Python

### Restarting Services

1. **Full Restart**:
   ```powershell
   # Stop all services
   taskkill /F /IM nginx.exe
   taskkill /F /IM python.exe
   
   # Start services
   .\commit_push_and_deploy.bat
   ```

2. **Nginx Only**:
   ```powershell
   taskkill /F /IM nginx.exe
   Start-Process -FilePath ".\nginx-1.27.5\nginx.exe" -NoNewWindow
   ```

### Application Errors

For application errors:

1. Check the application logs in `logs/casestrainer.log`
2. Verify the correct Python version is being used
3. Ensure all dependencies are installed with `pip install -r requirements.txt`

## Vue.js Frontend Development

To make changes to the Vue.js frontend:

1. Navigate to the `casestrainer-vue` directory
2. Make your changes to the Vue.js code
3. Build and deploy the frontend:
   ```
   .\scripts\build_and_deploy_vue.bat
   ```

## Important Notes

1. **NEVER** run the application directly with `python app_final_vue.py` without setting the proper host and port
2. Always use the provided batch scripts for starting the application
3. The application must run on port 5000 to match the Nginx proxy configuration
4. The host must be set to 0.0.0.0 (not localhost) to be accessible through the Nginx proxy
5. The Docker Nginx container must be running for external access

## Maintenance

### Regular Updates

1. Pull the latest code from the repository
2. Run `pip install -r requirements.txt` to update dependencies
3. Restart the application using the appropriate batch script

### Backup

Regularly backup the following:

1. The SQLite database (`citations.db`)
2. The `config.json` file containing API keys
3. Any custom modifications to the application code

## Security Considerations

1. The `SECRET_KEY` should be a strong, random value stored in `config.json`
2. API keys should never be committed to the repository
3. The application uses HTTPS for external access through the Nginx proxy
4. Session cookies are configured with secure settings
