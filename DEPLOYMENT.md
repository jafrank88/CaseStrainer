# CaseStrainer Deployment Guide

---

## Quick Start for New Contributors

- **Use only `start_casestrainer.bat` to start/restart the backend and Nginx.**
- **Build the Vue.js frontend with `build_and_deploy_vue.bat`.**
- **All API endpoints must use the `/casestrainer/api/` prefix.**
- **Copy `.env.example` to `.env` and fill in your secrets. Never commit real secrets!**
- **.env is already in .gitignore.**
- **Install pre-commit hooks for secret scanning and linting:**
  ```bash
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```
- **See this file and `docs/DEPLOYMENT_VUE.md` for troubleshooting and rollback.**
- **Check logs in the `logs/` directory if issues arise.**

---

This document provides comprehensive instructions for deploying and maintaining the CaseStrainer application with its Vue.js frontend.

## Deployment Architecture

CaseStrainer uses a multi-tier architecture:

1. **Frontend**: Vue.js application served by Flask
2. **Backend**: Flask application with RESTful API endpoints
3. **Proxy**: Windows Nginx for external access
4. **Database**: SQLite database for citation storage

## System Requirements

- Python 3.8+ with pip
- Windows Nginx for the proxy server
- Node.js and npm for Vue.js frontend development (only needed for frontend changes)
- Port 5000 must be available for the application
- Windows environment with PowerShell or Command Prompt

## Deployment Steps

### 1. Standard Deployment

For regular deployment, use the `start_casestrainer.bat` script:

```
.\start_casestrainer.bat
```

This script:
- Checks and stops any Windows Nginx instances to avoid conflicts
- Ensures port 5000 is available and kills any conflicting processes
- Installs/updates dependencies from requirements.txt
- Starts CaseStrainer with the correct host (0.0.0.0) and port (5000) settings

### 2. Nginx Proxy Deployment

For deployment with the Nginx proxy (recommended for production), use the unified script `start_casestrainer.bat` as described above. 

**Note:** The old script `scripts\start_for_nginx.bat` is deprecated and should not be used. All startup and restart operations must use `start_casestrainer.bat`.

## Access URLs

- **External access** (through Nginx proxy): https://wolf.law.uw.edu/casestrainer/
- **Local access** (direct): http://127.0.0.1:5000/

## Frontend Deployment

See `docs/DEPLOYMENT_VUE.md` for instructions on building and deploying the Vue.js frontend.

## Troubleshooting
- If you see a 502 Bad Gateway error, check that the Flask application is running on port 5000 and Nginx is properly configured.
- If you see path or 404 errors, ensure the Nginx proxy and frontend are using the `/casestrainer` prefix and API endpoints are under `/casestrainer/api/`.

### API Base Path

All API endpoints are accessed under the `/casestrainer/api/` prefix. For example:
- `https://wolf.law.uw.edu/casestrainer/api/verify_citation`
- `http://localhost:5000/casestrainer/api/verify_citation`

**Troubleshooting:**
If you encounter 404 or path errors, ensure both the frontend and backend use the `/casestrainer/api/` prefix and your Nginx/proxy configuration is correct.

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

### 2. Nginx Configuration

The Docker Nginx container is configured to proxy requests from `/casestrainer/` to the application running on port 5000.

Key Nginx configuration settings:
- External URL: https://wolf.law.uw.edu/casestrainer/
- Proxy pass: http://127.0.0.1:5000/
- X-Forwarded-Prefix: /casestrainer

## Troubleshooting

### Port Conflicts

If you receive an error about port 5000 being in use:

1. Manually identify the process using the port:
   ```
   netstat -ano | findstr :5000
   ```

2. Kill the process:
   ```
   taskkill /F /PID <process_id>
   ```

### Nginx Conflicts

If you experience issues with URL routing or proxy settings:

1. Ensure Windows Nginx is stopped:
   ```
   taskkill /F /IM nginx.exe
   ```

2. Verify the Docker Nginx container is running:
   ```
   docker ps | findstr "docker-nginx-1"
   ```

3. Check Nginx logs for errors:
   ```
   docker logs docker-nginx-1
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
