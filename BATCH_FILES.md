# CaseStrainer Batch Files Documentation

This document explains the purpose and usage of each batch file in the CaseStrainer project.

## Primary Deployment Scripts

### 1. `scripts\start_for_nginx.bat` - PRODUCTION DEPLOYMENT
**Purpose**: Primary script for production deployment with Nginx proxy
- Performs thorough checks for Windows Nginx conflicts
- Verifies Docker and Docker Nginx container status
- Frees port 5000 if it's in use
- Sets proper environment variables for production
- Starts app_final_vue.py with waitress server for production
- Makes the application accessible at https://wolf.law.uw.edu/casestrainer/

**Usage**: Run this script when deploying to the production server with Nginx proxy

### 2. `start_casestrainer_new.bat` - FLEXIBLE DEPLOYMENT
**Purpose**: Flexible script that supports both development and production modes
- Supports both development and production modes
- More robust port 5000 checking with multiple fallback methods
- Restarts Docker Nginx container to ensure latest changes
- Installs dependencies automatically
- In production mode, uses app_final_vue.py with Vue.js integration

**Usage**: 
- For development: `start_casestrainer_new.bat dev`
- For production: `start_casestrainer_new.bat`

## Other Deployment Scripts

### 3. `start_casestrainer.bat`
**Purpose**: Original production script with Vue.js integration
- Sets up environment for Vue.js integration
- Checks for Windows Nginx conflicts
- Verifies port 5000 availability
- Installs dependencies

**Status**: Superseded by `scripts\start_for_nginx.bat` - can be deprecated

### 4. `scripts\start_casestrainer.bat`
**Purpose**: Comprehensive production script
- Includes administrator privilege check
- Detects local IP address
- Attempts to start Docker Desktop if not running
- Uses run_production.py which includes additional checks

**Status**: Useful as a fallback if `scripts\start_for_nginx.bat` fails

## Build and Deployment Scripts

### 5. `scripts\build_and_deploy_vue.bat`
**Purpose**: Builds the Vue.js frontend and deploys it to the static directory
- Checks for Node.js and npm
- Installs Vue.js dependencies
- Builds the Vue.js frontend
- Copies the built files to the static/vue directory

**Usage**: Run this script when making changes to the Vue.js frontend

### 6. `start_vue.bat` (Planned/Not Implemented)
**Purpose**: Simplified script to start the Vue.js version of CaseStrainer
- Would likely start app_vue.py instead of app_final_vue.py
- Mentioned in .gitignore but not currently implemented

**Status**: Planned for future implementation

### 7. `install_vue_dependencies.bat` (Planned/Not Implemented)
**Purpose**: Script to install Vue.js specific dependencies
- Would likely install both Python and Node.js dependencies
- Mentioned in .gitignore but not currently implemented

**Status**: Planned for future implementation

### 8. `update_nginx_config.bat` (Planned/Not Implemented)
**Purpose**: Script to update the Nginx configuration
- Would likely update the Docker Nginx configuration to point to the correct port
- Mentioned in the memory about port changes from 5001 to 5000
- Mentioned in .gitignore but not currently implemented

**Status**: Planned for future implementation

## Recommended Usage

1. For normal production deployment:
   ```
   scripts\start_for_nginx.bat
   ```

2. For local development:
   ```
   start_casestrainer_new.bat dev
   ```

3. When updating the Vue.js frontend:
   ```
   scripts\build_and_deploy_vue.bat
   ```
   Then deploy with one of the above scripts.
