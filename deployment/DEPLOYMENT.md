Analysis Results

Not Found
# CaseStrainer Deployment Guide

This comprehensive guide provides instructions for deploying CaseStrainer to production environments, with specific focus on the current deployment at wolf.law.uw.edu/casestrainer.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- CourtListener API key (stored as environment variable)
- LangSearch API key (stored as environment variable)
- Docker (for the current production setup)
- Nginx (for proxying requests)

## Current System Architecture

CaseStrainer is currently deployed with the following architecture:

1. **External Access**: https://wolf.law.uw.edu/casestrainer/
2. **Docker Nginx Proxy**: Container handling SSL termination and routing
3. **Frontend Container**: Vue.js application served by Nginx
4. **Backend Container**: Python Flask application with Waitress WSGI server
5. **Redis Container**: Background task processing and caching
6. **RQ Worker Containers**: Multiple workers for async citation processing

## Docker Production Setup

The application uses Docker Compose for production deployment with the following services:

- **Nginx**: SSL termination and reverse proxy (ports 80/443)
- **Frontend**: Vue.js application (port 8080)
- **Backend**: Flask API server (port 5001)
- **Redis**: Task queue and caching (port 6380)
- **RQ Workers**: Background task processing (3 instances)

## Quick Start (Recommended)

### Using the Launcher Script

```powershell
# Start production deployment
.\launcher.ps1 -Environment DockerProduction
```

This will:
- Build the Vue.js frontend
- Start all Docker containers
- Configure SSL and routing
- Make the application available at https://wolf.law.uw.edu/casestrainer/

### Manual Docker Deployment

```powershell
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Legacy Windows Native Setup

For non-Docker deployments, the application can run directly on Windows:

### Application Server

The CaseStrainer application runs as a Python Flask application using Waitress as the WSGI server.

- **Host**: 0.0.0.0 (IMPORTANT: Must listen on all interfaces, not just localhost)
- **Port**: 5000
- **Startup Command**: `python src/app_final_vue.py --host 0.0.0.0 --port 5000`

### Important Notes About Legacy Setup

1. **Port Configuration**: The application must run on port 5000 to match the Nginx configuration.

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
- waitress
- eyecite
- redis
- rq

### 2. Configure API Keys (Secure Setup)

**Important**: API keys should be stored as environment variables, not in config files.

#### Setting Environment Variables

**Windows (PowerShell):**
```powershell
$env:COURTLISTENER_API_KEY="your_courtlistener_api_key_here"
$env:LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

**Linux/macOS (bash):**
```bash
export COURTLISTENER_API_KEY="your_courtlistener_api_key_here"
export LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

**Docker Environment:**
```powershell
# Set environment variables for Docker containers
docker-compose -f docker-compose.prod.yml up -d --build \
  -e COURTLISTENER_API_KEY="your_courtlistener_api_key_here" \
  -e LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

#### Required API Keys
- **CourtListener API Key**: For citation verification and canonical data lookup
  - Get your key at: https://www.courtlistener.com/help/api/rest/
- **LangSearch API Key**: For advanced text analysis (if using LangSearch features)

#### Security Best Practices
- ✅ Store keys as environment variables
- ✅ Never commit API keys to version control
- ✅ Use different keys for development and production
- ✅ Rotate keys regularly
- ❌ Don't store keys in config files
- ❌ Don't hardcode keys in source code

**Note**: The old `config.json` method is deprecated. Environment variables are now required for secure operation.

## Deployment Steps

### Docker Production (Recommended)

1. **Start with launcher**:
   ```powershell
   .\launcher.ps1 -Environment DockerProduction
   ```

2. **Or manual deployment**:
   ```powershell
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Access the application**: https://wolf.law.uw.edu/casestrainer/

### Legacy Windows Native

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

## Troubleshooting

### Common Issues

#### 1. 404 Errors on Frontend
- **Cause**: Frontend container not serving assets correctly
- **Solution**: Rebuild frontend container: `docker-compose -f docker-compose.prod.yml build frontend-prod`

#### 2. 500 Errors on API Calls
- **Cause**: Redis container stopped or backend can't connect
- **Solution**: Start Redis: `docker start casestrainer-redis-prod`

#### 3. Frontend Stuck on "Waiting for backend"
- **Cause**: Container networking issue
- **Solution**: Rebuild frontend: `docker-compose -f docker-compose.prod.yml build frontend-prod`

#### 4. Assets Not Loading (JS/CSS 404)
- **Cause**: Nginx not routing `/assets/` requests correctly
- **Solution**: Restart Nginx: `docker restart casestrainer-nginx-prod`

### Health Checks

```powershell
# Check all containers
docker ps

# Check backend health
curl http://localhost:5001/casestrainer/api/health

# Check Redis connection
docker exec casestrainer-redis-prod redis-cli ping

# Check frontend
curl http://localhost:8080/casestrainer/
```

## Maintenance and Updates

### Updating the Application

1. Pull the latest changes from the repository:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart Docker services:
   ```powershell
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. Or use the launcher:
   ```powershell
   .\launcher.ps1 -Environment DockerProduction
   ```

### Monitoring

Monitor the application logs for errors and performance issues:

- **Backend logs**: `docker logs casestrainer-backend-prod`
- **Frontend logs**: `docker logs casestrainer-frontend-prod`
- **Nginx logs**: `docker logs casestrainer-nginx-prod`
- **Redis logs**: `docker logs casestrainer-redis-prod`

## Security Considerations

1. **API Keys**: Store API keys securely in `config.json` and ensure this file is not committed to version control.

2. **SSL/TLS**: The current setup uses SSL/TLS for secure communication. Ensure certificates are kept up to date.

3. **File Uploads**: The application validates file types and implements proper error handling for file uploads.

4. **Container Security**: All containers run with appropriate resource limits and health checks.

## Contact and Support

For issues or questions about the deployment, contact the system administrator or refer to the project documentation.
