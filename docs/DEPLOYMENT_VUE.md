# CaseStrainer Vue.js Deployment Guide

This guide provides comprehensive instructions for deploying the Vue.js version of CaseStrainer to the production server at https://wolf.law.uw.edu/casestrainer/.

## Overview

The Vue.js version of CaseStrainer represents a complete modernization of the application with:

- A modern, responsive user interface built with Vue.js
- Clear separation between frontend and backend (API-driven architecture)
- Improved maintainability and extensibility
- Support for all existing features plus planned enhancements

**IMPORTANT: The Vue.js frontend and backend API are now working correctly and deployed at https://wolf.law.uw.edu/casestrainer/**

## Prerequisites

- Python 3.8+ with pip
- Node.js 14+ and npm 6+ (for building the Vue.js frontend)
- Docker (for the Nginx proxy container)
- Git (for version control)

## Files and Components

1. **Backend API (`vue_api.py`)** - Flask Blueprint with all API endpoints
2. **Application Entry Point (`app_vue.py`)** - Main Flask application serving Vue.js frontend and API
3. **Vue.js Frontend** - Located in the `casestrainer-vue` directory
4. **Deployment Scripts**:
   - `build_and_deploy_vue.bat` - Builds and deploys the Vue.js frontend
   - `start_vue.bat` - Starts the application with proper settings

## Deployment Steps

### 1. Install Dependencies

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Build and Deploy the Vue.js Frontend

Run the build script to compile the Vue.js frontend and copy it to the correct location:

```bash
.\build_and_deploy_vue.bat
```

This script will:
- Install npm dependencies
- Build the Vue.js frontend for production
- Copy the built files to the `static/vue` directory

> **Note**: This step requires Node.js and npm to be installed. If you don't have them, you can download from https://nodejs.org/.

### 3. Configure the Environment

Ensure the application is configured to run on port 5000 and listen on all interfaces (0.0.0.0):

```bash
set HOST=0.0.0.0
set PORT=5000
set USE_CHEROOT=True
```

### 4. Start the Application

Start the CaseStrainer application with the Vue.js frontend using the dedicated script for Nginx deployment:

```bash
.\start_for_nginx.bat
```

This script will:
- Check for and stop any conflicting processes (including Windows Nginx)
- Ensure Docker and the Nginx container are running
- Start the application on port 5000 with host 0.0.0.0
- Configure the application to use the Cheroot WSGI server for production deployment

Alternatively, you can use the updated start script:

```bash
.\start_casestrainer_updated.bat
```

### 5. Verify the Deployment

After deployment, verify that the application is working correctly:

1. Visit https://wolf.law.uw.edu/casestrainer/
2. Confirm that the modern Vue.js interface loads
3. Test key features:
   - Citation verification
   - Unconfirmed citations view
   - Multitool confirmed citations
   - Citation network visualization
   - ML classifier (if implemented)

## Docker Nginx Configuration

The application is accessed through a Docker Nginx container that proxies requests to the Flask application.

Key points:
- The Docker container name is `docker-nginx-1`
- Nginx is configured to forward requests from `/casestrainer/` to the Flask application on port 5000
- The Flask application uses a `PrefixMiddleware` to handle the `/casestrainer/` prefix

**VERIFIED CONFIGURATION:**
- The Docker Nginx container is correctly configured to proxy requests to 10.158.120.151:5000
- The configuration file is located at `/etc/nginx/conf.d/casestrainer.conf` in the Docker container
- The application must run on port 5000 (not 5001 or any other port) to work with the Nginx proxy

## Troubleshooting

### 502 Bad Gateway Error

If you see a 502 Bad Gateway error when accessing the application:

1. Ensure the Flask application is running on port 5000
2. Verify that it's listening on all interfaces (`0.0.0.0`, not just `127.0.0.1`)
   ```bash
   netstat -ano | findstr :5000
   ```
   You should see `0.0.0.0:5000` in the output, not `127.0.0.1:5000`

3. Check that the Docker Nginx container is running:
   ```bash
   docker ps | findstr nginx
   ```

4. Verify the Nginx configuration is correctly pointing to your server IP and port 5000:
   ```bash
   docker exec docker-nginx-1 cat /etc/nginx/conf.d/casestrainer.conf
   ```
   Ensure the proxy_pass line shows: `proxy_pass http://10.158.120.151:5000/;`

5. If the Nginx configuration is incorrect, update it and reload:
   ```bash
   docker exec docker-nginx-1 sh -c "sed -i 's/proxy_pass http:\/\/10.158.120.151:8080\//proxy_pass http:\/\/10.158.120.151:5000\//g' /etc/nginx/conf.d/casestrainer.conf"
   docker exec docker-nginx-1 nginx -s reload
   ```
   
6. Run the update_nginx_config.bat script to automatically update the Nginx configuration:
   ```bash
   .\update_nginx_config.bat
   ```

### Vue.js Build Issues

If you encounter issues building the Vue.js frontend:

1. Ensure Node.js and npm are installed and in your PATH
2. Try clearing the npm cache:
   ```bash
   npm cache clean --force
   ```
3. Delete the `node_modules` directory and reinstall dependencies:
   ```bash
   cd casestrainer-vue
   rm -rf node_modules
   npm install
   ```

## API Endpoints

The Vue.js frontend communicates with the backend through these API endpoints:

- `/api/analyze` - Analyze briefs for citations
- `/api/unconfirmed_citations_data` - Get unconfirmed citations
- `/api/confirmed_with_multitool_data` - Get citations confirmed with multiple tools
- `/api/citation_network_data` - Get citation network visualization data
- `/api/train_ml_classifier` - Train the ML classifier
- `/api/classify_citation` - Classify a citation using ML
- `/api/test_citations` - Get test citations
- `/api/verify_citation` - Verify a single citation

## Updating the Application

To update the application:

1. Pull the latest changes from the repository:
   ```bash
   git pull origin main
   ```

2. Rebuild the Vue.js frontend:
   ```bash
   .\build_and_deploy_vue.bat
   ```

3. Restart the application:
   ```bash
   .\start_vue.bat
   ```

## Rollback Procedure

If you need to roll back to the original version:

1. Stop the Vue.js version:
   ```bash
   taskkill /F /IM python.exe
   ```

2. Start the original version:
   ```bash
   python app_final.py --host=0.0.0.0 --port=5000
   ```

## Security Considerations

- API keys for CourtListener and LangSearch are stored in `config.json`
- The application uses HTTPS through the Nginx proxy
- Ensure file permissions are set correctly on the server
- Keep all dependencies updated to patch security vulnerabilities
