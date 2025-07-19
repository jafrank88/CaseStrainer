# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# CaseStrainer Deployment Guide

# CaseStrainer Deployment Guide

## Environment Variables Setup

### Required Configuration

1. **Create a `.env` file**:
   ```bash
   cp .env.template .env
   ```

2. **Configure the `.env` file**:
   - Set `COURTLISTENER_API_KEY` with your CourtListener API key
   - Configure database settings
   - Set up email settings for notifications
   - Adjust other settings as needed

### Obtaining a CourtListener API Key

1. Go to [CourtListener API Registration](https://www.courtlistener.com/api/rest-info/)
2. Sign up for an account if you don't have one
3. Generate a new API key from your account settings
4. Copy the API key to your `.env` file:
   ```
   COURTLISTENER_API_KEY=your-api-key-here
   ```

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `COURTLISTENER_API_KEY` | Yes | API key for CourtListener | `abc123...` |
| `FLASK_ENV` | No | Application environment | `production` |
| `SECRET_KEY` | Yes | Flask secret key | `your-secret-key` |
| `DATABASE_URI` | Yes | Database connection string | `sqlite:///instance/casestrainer.db` |
| `MAIL_SERVER` | Yes | SMTP server | `smtp.uw.edu` |
| `MAIL_PORT` | Yes | SMTP port | `587` |
| `MAIL_USE_TLS` | Yes | Use TLS | `True` |
| `MAIL_USERNAME` | Yes | SMTP username | `your-netid` |
| `MAIL_PASSWORD` | Yes | SMTP password | `your-password` |
| `MAIL_DEFAULT_SENDER` | Yes | Default sender email | `your-email@uw.edu` |

## Quick Start for New Contributors

### Core Scripts

- **`start_casestrainer.bat`** - Main script to start both backend and Nginx
- **`debug_flask.bat`** - Start Flask in debug mode for development
- **`build_frontend.bat`** - Build the Vue.js frontend
- **`run_tests.bat`** - Run the test suite
- **`update_nginx_config.bat`** - Update Nginx configuration
- **`commit_push_and_deploy.bat`** - Helper for deployment workflow

### First-Time Setup

1. Clone the repository

2. Create and activate a Python virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure your environment variables

5. Build the frontend:

   ```bash
   build_frontend.bat
   ```

6. Start the application:

   ```bash
   start_casestrainer.bat
   ```

### Development Workflow

- **For backend development**: Use `debug_flask.bat`
- **For frontend development**: Use `build_frontend.bat` after making changes
- **For testing**: Use `run_tests.bat`

### Logs

- Application logs: `logs/`
- Nginx logs: `nginx-1.27.5/logs/`

## Production Server Options

### Option 1: Waitress (Recommended for Windows)

Waitress is a pure-Python WSGI server that works well on Windows:

1. Install Waitress:

   ```bash
   pip install waitress
   ```

2. Run the application:

   ```bash
   waitress-serve --port=5000 --call 'wsgi:application'
   ```

### Option 2: Gunicorn (Recommended for Linux/Unix)

Gunicorn is a robust WSGI server (already included in requirements.txt):

1. Install Gunicorn (if not already installed):

   ```bash
   pip install gunicorn
   ```

2. Run the application:

   ```bash
   gunicorn --bind 0.0.0.0:5000 wsgi:application
   ```

### Running Behind Nginx

Both servers should be run behind Nginx in production. Example Nginx configuration:

```nginx
location /casestrainer/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /casestrainer;
}
```

## Overview

This document provides comprehensive deployment instructions for the CaseStrainer application, including both the Flask backend and Vue 3 frontend. The application is designed to run on Windows with Nginx as a reverse proxy.

> **IMPORTANT**: The Vue 3 frontend is now the default interface, located in the `casestrainer-vue-new` directory. The legacy jQuery interface has been removed.

## Deployment Architecture

CaseStrainer uses a multi-tier architecture:

1. **Frontend Build**: The Vue.js application is built into static files located in `casestrainer-vue-new/dist/`
2. **Flask Serving**: The Flask application serves these static files and handles API requests
3. **Nginx Proxy**: External requests are proxied through Nginx for HTTPS termination and load balancing
4. **Database**: SQLite database for citation storage
5. **SSL/TLS**: Managed by Nginx with Let's Encrypt certificates

### Directory Structure

```text
CaseStrainer/
├── casestrainer-vue-new/    # Vue 3 frontend source
│   ├── src/                 # Vue source files
│   ├── public/              # Static assets
│   └── package.json         # Frontend dependencies
├── src/                     # Python backend
│   ├── app_final_vue.py     # Main Flask application
│   └── ...
├── nginx-1.27.5/           # Nginx installation
└── logs/                    # Application logs
```

### Access Points

- **Main Application**: `https://wolf.law.uw.edu/casestrainer/`
- **API Endpoint**: `https://wolf.law.uw.edu/casestrainer/api/analyze` (proxied to `http://localhost:5000/api/analyze`)
- **Local Development**: `http://localhost:5000/`
  - Local API: `http://localhost:5000/api/...`

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
- Start the Flask development server on [http://localhost:5000/](http://localhost:5000/)

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
   - Access the application at `https://wolf.law.uw.edu/casestrainer/`
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

- **External access** (through Nginx proxy): `https://wolf.law.uw.edu/casestrainer/`
- **Local access** (direct): `http://127.0.0.1:5000/`

## Frontend Deployment

See [Vue.js Deployment Guide](docs/DEPLOYMENT_VUE.md) for instructions on building and deploying the Vue.js frontend.

## Troubleshooting

Common issues and solutions:

- **502 Bad Gateway**: Check that the Flask application is running on port 5000 and Nginx is properly configured.
- **404 Not Found**: Ensure the Nginx proxy and frontend are using the `/casestrainer` prefix and API endpoints are under `/casestrainer/api/`.
- **405 Method Not Allowed**: Verify that the correct HTTP method is being used for each endpoint.

## API Configuration

### Base Path

All API endpoints use the `/casestrainer/api/` prefix. Example endpoints:

- **File Analysis**: `POST /casestrainer/api/analyze`
- **Text Analysis**: `POST /casestrainer/api/analyze`
- **URL Analysis**: `POST /casestrainer/api/analyze`

### Important Notes

## Frontend Configuration

- Must use absolute paths with the `/casestrainer` prefix
- API requests should be made to `/casestrainer/api/*`

## Backend Configuration

- Flask routes are registered with the `/api` prefix in `app_final_vue.py`
- Nginx handles the `/casestrainer` prefix

## Troubleshooting Common Issues

- **404 errors**: Check path prefixes in both frontend and backend
- **405 Method Not Allowed**: Verify the HTTP method matches the endpoint
- **502 Bad Gateway**: Ensure Flask is running on port 5000

### Startup Script

Always use `start_casestrainer.bat` to start or restart the application. All other batch files are archived and unsupported.

## Configuration Files

### Application Configuration

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

## Nginx Configuration

### Nginx Key Settings

- **SSL Certificates**: Located at `D:/CaseStrainer/ssl/`
- **Proxy Target**: `http://127.0.0.1:5000`
- **URL Prefix**: `/casestrainer`
- **Headers**: `X-Forwarded-Prefix` is set for proper URL generation

### Nginx Configuration Notes

1. **No Trailing Slash**: The `proxy_pass` directive should NOT have a trailing slash
2. **Required Headers**: `X-Forwarded-Prefix` is essential for proper URL generation
3. **Hostnames**: All possible hostnames are included in `server_name`

## Troubleshooting

### Common Issues

#### 502 Bad Gateway

- **Cause**: Flask application not running or not accessible on port 5000
- **Solution**:

  ```powershell
  # Check if Flask is running
  netstat -ano | findstr :5000
  
  # If not, start it manually
  python src/app_final_vue.py --host=0.0.0.0 --port=5000
  ```

#### 404 Not Found

- **Cause**: Incorrect URL path or Nginx configuration
- **Solution**:
  - Verify the URL includes `/casestrainer/` prefix
  - Check Nginx configuration for proper `proxy_pass` settings
  - Ensure Flask routes are correctly prefixed with `/api`

#### 405 Method Not Allowed

- **Cause**: Incorrect HTTP method used for the endpoint
- **Solution**:
  - Check the API documentation for the correct HTTP method
  - Verify the endpoint URL is correct

### Log Files

1. **Nginx Error Log**:

   ```plaintext
   nginx-1.27.5/logs/casestrainer_error.log
   ```

2. **Application Logs**:

   ```plaintext
   logs/casestrainer.log
   ```

3. **Windows Event Log**:

   - Check for system-level errors related to Nginx or Python

## Service Management

### Restarting Services

#### Full Restart

```powershell
# Stop all services
taskkill /F /IM nginx.exe
taskkill /F /IM python.exe

# Start services
.\commit_push_and_deploy.bat
```

#### Nginx Only

```powershell
# Stop Nginx
taskkill /F /IM nginx.exe

# Start Nginx
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

   ```bash
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
