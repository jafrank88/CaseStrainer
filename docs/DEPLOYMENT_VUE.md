# CaseStrainer Vue.js Deployment Guide

---

## Quick Start for New Contributors

- **Use `launcher.ps1` to start/restart all services in any environment.**
- **Build the Vue.js frontend with `build_and_deploy_vue.bat`.**
- **All API endpoints must use the `/casestrainer/api/` prefix.**
- **Copy `.env.example` to `.env` and fill in your secrets.**
  - Never commit real secrets!
  - `.env` is already in `.gitignore`
- **Install pre-commit hooks** for code quality and security:
  ```bash
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```
- **Check logs** in the `logs/` directory if issues arise
- **Docker logs** are available via `docker logs <container-name>`

---

This guide provides comprehensive instructions for deploying the Vue.js version of CaseStrainer using Docker containers and the PowerShell launcher.

## Overview

The Vue.js version of CaseStrainer represents a complete modernization of the application with:

- A modern, responsive user interface built with Vue 3 and Composition API
- Clear separation between frontend and backend (API-driven architecture)
- Docker containerization for consistent deployment
- Auto-restart system with health monitoring
- Redis-based task queue for background processing
- Improved maintainability and extensibility
- Support for all existing features plus planned enhancements
- Located in the `casestrainer-vue-new/` directory

**IMPORTANT: The Vue.js frontend and backend API are now working correctly and deployed with Docker containers**

### Frontend Structure

```
casestrainer-vue-new/
├── src/                # Vue source files
│   ├── assets/         # Static assets
│   ├── components/     # Vue components
│   ├── router/         # Vue Router configuration
│   ├── store/          # Pinia store modules
│   ├── views/          # Page components
│   ├── App.vue         # Root Vue component
│   └── main.js         # Application entry point
├── public/             # Static files
└── package.json        # Dependencies and scripts
```

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** and npm 8+ (LTS recommended)
- **Docker Desktop** for Windows with WSL 2 backend
- **Git** for version control
- **PowerShell** (included with Windows)

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB free space
- **Network**: Internet connection for API calls
- **Ports**: 5000, 5001, 6379 (Redis), 443, 80 (production)

## Deployment Options

### 1. Docker Production (Recommended)

```powershell
.\launcher.ps1 -Environment DockerProduction
```

This starts the complete production stack:

- **Backend**: Containerized Flask app with Waitress WSGI server
- **Frontend**: Nginx container serving Vue.js build
- **Redis**: Dedicated container with persistence
- **RQ Workers**: Multiple worker containers for background tasks
- **Nginx**: Reverse proxy with SSL support
- **Health Checks**: Automatic monitoring and recovery

### 2. Docker Development

```powershell
.\launcher.ps1 -Environment DockerDevelopment
```

This starts a development environment with:

- **Backend**: Containerized Flask development server
- **Frontend**: Containerized Vue.js dev server with hot reload
- **Redis**: Dedicated container
- **Volume mounts**: Live code changes

### 3. Local Development

```powershell
.\launcher.ps1 -Environment Development
```

This starts local services:

- **Backend**: Flask development server on port 5000
- **Frontend**: Vue.js dev server on port 5173
- **Redis**: Local or Docker container

### 4. Local Production

```powershell
.\launcher.ps1 -Environment Production
```

This starts local production services:

- **Backend**: Flask app with Waitress WSGI
- **Frontend**: Built and served by Flask
- **Nginx**: Reverse proxy on port 443

## Docker Configuration

### Production Stack (`docker-compose.prod.yml`)

```yaml
services:
  # Data Layer
  redis:
    image: redis:7-alpine
    container_name: casestrainer-redis-prod
    ports:
      - "6380:6379"
    volumes:
      - redis_data_prod:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 60s
      timeout: 30s
      retries: 8
      start_period: 180s

  # Application Layer
  backend:
    build: .
    container_name: casestrainer-backend-prod
    command: waitress-serve --port=5000 --threads=2 src.app_final_vue:app
    ports:
      - "5001:5000"
    depends_on:
      redis:
        condition: service_healthy
    env_file:
      - .env.production
    environment:
      - REDIS_URL=redis://casestrainer-redis-prod:6379/0
      - FLASK_ENV=production
      - FLASK_DEBUG=False
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    mem_limit: 2g
    mem_reservation: 1g
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/casestrainer/api/health"]
      interval: 60s
      timeout: 30s
      retries: 8
      start_period: 180s

  # Background Workers
  rqworker:
    build: .
    container_name: casestrainer-rqworker-prod
    command: python src/rq_worker.py worker casestrainer
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://casestrainer-redis-prod:6379/0
      - CASTRAINER_ENV=production
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "src/healthcheck_rq.py"]
      interval: 60s
      timeout: 30s
      retries: 8
      start_period: 180s

  # Frontend Production Build
  frontend-prod:
    build: 
      context: ./casestrainer-vue-new
      dockerfile: Dockerfile.prod
    container_name: casestrainer-frontend-prod
    ports:
      - "8080:80"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 60s
      timeout: 30s
      retries: 8
      start_period: 180s

  # Infrastructure Layer
  nginx:
    image: nginx:alpine
    container_name: casestrainer-nginx-prod
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/html
    depends_on:
      backend:
        condition: service_healthy
      frontend-prod:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:80/health || exit 1"]
      interval: 60s
      timeout: 30s
      retries: 8
      start_period: 180s
```

### Environment Configuration

Create `.env.production` for Docker production:

```ini
# Flask Configuration
FLASK_APP=src.app_final_vue
FLASK_ENV=production
SECRET_KEY=your-production-secret-key

# API Keys
COURTLISTENER_API_KEY=your-courtlistener-api-key
LANGSEARCH_API_KEY=your-langsearch-api-key

# Database
DATABASE_FILE=/app/data/citations.db

# Redis
REDIS_URL=redis://casestrainer-redis-prod:6379/0

# Email (UW SMTP)
MAIL_SERVER=smtp.uw.edu
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-netid
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-netid@uw.edu

# Worker Environment
CASTRAINER_ENV=production
```

## Files and Components

1. **Backend API (`src/vue_api_endpoints.py`)** - Flask Blueprint with all API endpoints
2. **Application Entry Point (`src/app_final_vue.py`)** - Main Flask application serving Vue.js frontend and API
3. **Vue.js Frontend** - Located in the `casestrainer-vue-new` directory
4. **Docker Configuration**:
   - `docker-compose.prod.yml` - Production Docker stack
   - `docker-compose.dev.yml` - Development Docker stack
   - `Dockerfile` - Backend container definition
   - `casestrainer-vue-new/Dockerfile.prod` - Frontend container definition
5. **Launcher Script**:
   - `launcher.ps1` - PowerShell launcher with auto-restart capabilities

## Deployment Steps

### 1. Install Dependencies

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Build and Deploy the Vue.js Frontend

Run the build script to compile the Vue.js frontend:

```bash
.\build_and_deploy_vue.bat
```

This script will:
- Install npm dependencies
- Build the Vue.js frontend for production
- Copy the built files to the `static/vue` directory

> **Note**: This step requires Node.js and npm to be installed. If you don't have them, you can download from https://nodejs.org/.

### 3. Configure Environment

Create the production environment file:

```bash
copy .env.example .env.production
```

Edit `.env.production` and set your configuration:

```ini
# Flask Configuration
FLASK_APP=src.app_final_vue
FLASK_ENV=production
SECRET_KEY=your-production-secret-key

# API Keys
COURTLISTENER_API_KEY=your-courtlistener-api-key
LANGSEARCH_API_KEY=your-langsearch-api-key

# Database
DATABASE_FILE=/app/data/citations.db

# Redis
REDIS_URL=redis://casestrainer-redis-prod:6379/0

# Email (UW SMTP)
MAIL_SERVER=smtp.uw.edu
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-netid
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-netid@uw.edu
```

### 4. Start Docker Production Stack

Use the launcher to start the complete production stack:

```powershell
.\launcher.ps1 -Environment DockerProduction
```

This will:
- Build Docker images if needed
- Start all containers with proper dependencies
- Configure health checks and monitoring
- Set up auto-restart capabilities

### 5. Verify the Deployment

After deployment, verify that the application is working correctly:

1. **Check container status**:
   ```powershell
   docker ps
   ```

2. **Check health status**:
   ```powershell
   .\launcher.ps1 -Environment DockerProduction -NoMenu
   ```

3. **Test endpoints**:
   - Backend health: `http://localhost:5001/casestrainer/api/health`
   - Frontend: `http://localhost:8080/`
   - Production: `https://localhost/casestrainer/`

4. **Test key features**:
   - Citation verification
   - Unconfirmed citations view
   - Multitool confirmed citations
   - Citation network visualization
   - ML classifier (if implemented)

## API Path and Prefix Consistency

- All API endpoints are available under `/casestrainer/api/`.

### API Base Path

All API endpoints are accessed under the `/casestrainer/api/` prefix. For example:
- `https://your-domain.com/casestrainer/api/analyze`
- `http://localhost:5001/casestrainer/api/analyze`

**Troubleshooting:**
If you encounter 404 or path errors, ensure your Nginx/proxy configuration is correctly handling the `/casestrainer` prefix and forwarding requests to the backend with the correct path.

## Health Checks and Monitoring

### Health Check Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **Backend Health** | http://localhost:5001/casestrainer/api/health | API server status |
| **Frontend (Dev)** | http://localhost:5173/ | Vue.js development server |
| **Production** | https://localhost/casestrainer/ | Production build |

### Health Check Criteria

- **Backend**: Responds to health API calls with timeout protection
- **Frontend**: Serves web pages correctly
- **Redis**: Accepts connections and responds to ping
- **RQ Worker**: Process is running and connected to Redis
- **Nginx**: Serves static files and proxies API calls

### Monitoring Dashboard

The system provides real-time monitoring through:

1. **Console Output**: Real-time status updates
2. **Crash Logs**: Detailed error tracking
3. **Health Checks**: Automated service validation
4. **Docker Logs**: Container-specific logs

## Troubleshooting

### 502 Bad Gateway Error

If you see a 502 Bad Gateway error when accessing the application:

1. **Check container status**:
   ```bash
   docker ps -a
   ```

2. **Check backend logs**:
   ```bash
   docker logs casestrainer-backend-prod
   ```

3. **Verify backend is running**:
   ```bash
   curl -f http://localhost:5001/casestrainer/api/health
   ```

4. **Check Nginx configuration**:
   ```bash
   docker exec casestrainer-nginx-prod nginx -t
   ```

### Container Issues

1. **Container won't start**:
   ```bash
   docker logs <container-name>
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Health check failures**:
   ```bash
   docker inspect <container-name> | grep -A 10 Health
   ```

3. **Resource issues**:
   ```bash
   docker stats
   ```

### Common Issues

- **Port conflicts**: Ensure ports 5000, 5001, 6379, 443, 80 are available
- **Redis connection errors**: Check if Redis container is running
- **Frontend not loading**: Verify Vue.js build is complete
- **Health check failures**: Recent fixes implemented - check launcher logs

### Emergency Procedures

1. **Stop all services**:
   ```powershell
   .\launcher.ps1 -Environment DockerProduction -NoMenu
   # Select option 4: Stop All Services
   ```

2. **Restart Docker Desktop**:
   - Close Docker Desktop
   - Restart Docker Desktop
   - Wait for it to become available

3. **Clean restart**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker system prune -f
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Security Checklist

- [ ] All secrets and sensitive configuration stored in `.env.production`
- [ ] `.env.production` and other sensitive files included in `.gitignore`
- [ ] SSL certificates properly configured in Nginx
- [ ] API keys secured and not committed to version control
- [ ] Pre-commit hooks installed for secret scanning
- [ ] Health checks implemented for all services
- [ ] Resource limits configured for containers
- [ ] Logging configured for security monitoring

## Performance Optimization

### Docker Resource Limits

```yaml
# Backend container
mem_limit: 2g
mem_reservation: 1g

# RQ Worker containers
mem_limit: 1g
mem_reservation: 512m
```

### Waitress Configuration

```python
# Production WSGI server
waitress-serve --port=5000 --threads=2 src.app_final_vue:app
```

### Redis Persistence

```yaml
# Redis container with persistence
volumes:
  - redis_data_prod:/data
```

## Backup and Recovery

### Database Backup

```bash
# Backup SQLite database
docker exec casestrainer-backend-prod sqlite3 /app/data/citations.db ".backup /app/data/citations_backup.db"

# Copy backup to host
docker cp casestrainer-backend-prod:/app/data/citations_backup.db ./data/
```

### Configuration Backup

```bash
# Backup environment files
cp .env.production .env.production.backup

# Backup Docker volumes
docker run --rm -v casestrainer_redis_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

## Support

For issues and feature requests, please create an issue in the GitHub repository.

### Getting Help

1. **Check logs**: `logs/` directory and Docker logs
2. **Health checks**: Use launcher menu option 5
3. **Documentation**: Review this guide and other docs
4. **GitHub issues**: Report bugs and request features
