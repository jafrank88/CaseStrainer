# CaseStrainer Deployment Guide

This document provides instructions for deploying and running the CaseStrainer application with its Vue.js frontend.

## System Requirements

- Python 3.13.3 (installed at `D:\Python\python.exe`)
- Node.js (installed at `D:\node.exe`)
- npm modules (installed at `D:\node_modules`)
- Docker for Nginx proxy (configured to forward requests from https://wolf.law.uw.edu/casestrainer/ to localhost:5000)

## Installation and Setup

### 1. Clone the Repository

If you haven't already, clone the repository to your local machine:

```bash
git clone https://github.com/jafrank88/CaseStrainer.git
cd CaseStrainer
```

### 2. Install Python Dependencies

The application requires several Python packages. Install them using:

```bash
D:\Python\python.exe -m pip install -r requirements.txt
```

### 3. Build the Vue.js Frontend

To build the Vue.js frontend and deploy it to the static/vue directory:

```bash
.\build_and_deploy_vue.bat
```

This script:
- Installs Node.js dependencies
- Builds the Vue.js frontend
- Copies the built files to the static/vue directory

## Running the Application

### Option 1: Run with Vue.js Frontend (Integrated)

To run the application with the Vue.js frontend integrated into the Flask application:

```bash
.\start_with_d_python.bat
```

This will:
- Check if port 5000 is available
- Start the Flask application with the Vue.js frontend
- Make the application accessible at:
  - Local: http://localhost:5000
  - External: https://wolf.law.uw.edu/casestrainer/

### Option 2: Run with Vue.js Development Server

To run the application with the Vue.js development server (for frontend development):

```bash
.\start_casestrainer_vue.bat
```

This will:
- Start the Flask backend on port 5000
- Start the Vue.js development server on port 8080
- Make the application accessible at:
  - Backend: http://localhost:5000
  - Frontend: http://localhost:8080
  - External (via Nginx): https://wolf.law.uw.edu/casestrainer/

## Application Structure

The CaseStrainer application has a dual-interface approach:

1. **Modern Vue.js Frontend**:
   - Landing page at the root URL: `/` or `/casestrainer/`
   - Vue.js static files served from `/vue/` or `/casestrainer/vue/`

2. **Original CaseStrainer Interface**:
   - Accessible at `/api/` or `/casestrainer/api/`
   - Contains all the original functionality

## Troubleshooting

### Port 5000 Already in Use

If port 5000 is already in use, the startup scripts will attempt to kill the process using the port. If this fails, you can manually find and kill the process:

```bash
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### Python Not Found

If you encounter issues with Python not being found, ensure that:
- Python is installed at `D:\Python\python.exe`
- The startup scripts are using the correct path to the Python executable

### Node.js Not Found

If you encounter issues with Node.js not being found, ensure that:
- Node.js is installed at `D:\node.exe`
- npm modules are installed at `D:\node_modules`
- The build script is using the correct paths

## Nginx Configuration

The application is configured to work with an Nginx proxy that forwards requests from https://wolf.law.uw.edu/casestrainer/ to the local server on port 5000. The Nginx configuration is managed through Docker.

To check the status of the Nginx container:

```bash
docker ps | findstr nginx
```

If the Nginx container is not running, start it with:

```bash
docker start docker-nginx-1
```

## Updating the Application

To update the application:

1. Pull the latest changes from the repository
2. Install any new Python dependencies
3. Rebuild the Vue.js frontend
4. Restart the application

```bash
git pull
D:\Python\python.exe -m pip install -r requirements.txt
.\build_and_deploy_vue.bat
.\start_with_d_python.bat
```
