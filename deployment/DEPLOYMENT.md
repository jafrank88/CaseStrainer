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
- **Startup Command**: `python src/app_final_vue.py --host 0.0.0.0 --port 5000`

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

## Deployment Steps

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
   python src/app_final_vue.py --host 0.0.0.0 --port 5000
   ```
   
   > **CRITICAL**: The application must listen on all interfaces (0.0.0.0), not just localhost (127.0.0.1), so the Docker container can reach it at 10.158.120.151:5000. This is the most common cause of deployment issues - binding to 127.0.0.1 instead of 0.0.0.0 will prevent the Docker container from connecting to the application.

4. **Verify Docker Nginx is running**:
   ```powershell
   docker ps | findstr nginx
   ```

5. **Access the application**: https://wolf.law.uw.edu/casestrainer/

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
