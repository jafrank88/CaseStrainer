# CaseStrainer

A production-ready legal citation analysis and verification system with Docker deployment, Vue.js frontend, and Flask backend.

## 🚀 Quick Start

### Production Deployment (Recommended)

```powershell
# Start production deployment with Docker
.\launcher.ps1 -Environment DockerProduction
```

This will:
- Build the Vue.js frontend
- Start all Docker containers (Nginx, Frontend, Backend, Redis, RQ Workers)
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

## 🏗️ Architecture

CaseStrainer uses a modern microservices architecture:

- **Nginx**: SSL termination and reverse proxy (ports 80/443)
- **Frontend**: Vue.js application served by Nginx (port 8080)
- **Backend**: Flask API server with Waitress WSGI (port 5001)
- **Redis**: Task queue and caching (port 6380)
- **RQ Workers**: Background task processing (3 instances)

## ✨ Features

### Citation Analysis
- **Multi-format Support**: PDF, DOCX, RTF, and text files
- **Enhanced Extraction**: Advanced case name and date extraction
- **Parallel Citations**: Detection and display of parallel citations (e.g., "302 P.3d 156")
- **Verification**: CourtListener API integration for citation verification
- **Complex Citations**: Handling of complex citations with multiple components

### Production Features
- **Docker Deployment**: Complete containerized production setup
- **Async Processing**: Redis-based task queue for large documents
- **Health Monitoring**: Comprehensive health checks and monitoring
- **SSL/TLS**: Production-ready SSL configuration
- **Resource Management**: CPU and memory limits for stability

### User Interface
- **Modern Vue.js Frontend**: Responsive web interface
- **Real-time Progress**: Progress tracking for long-running operations
- **Detailed Results**: Comprehensive citation analysis with metadata
- **Export Options**: Copy results and download functionality

## 📋 Requirements

- Docker and Docker Compose
- Node.js 16+ (for frontend development)
- Python 3.8+ (for backend development)
- CourtListener API key
- LangSearch API key

## 🔧 Configuration

### API Keys
Create `config.json` in the project root:
```json
{
  "courtlistener_api_key": "your_courtlistener_api_key_here",
  "langsearch_api_key": "your_langsearch_api_key_here"
}
```

### Environment Variables
- `VITE_APP_ENV`: Set to "production" for production builds
- `NODE_ENV`: Set to "production" for optimized builds

## 🚀 Deployment

### Production Deployment
1. **Using Launcher Script** (Recommended):
   ```powershell
   .\launcher.ps1 -Environment DockerProduction
   ```

2. **Manual Deployment**:
   ```powershell
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Access Application**: https://wolf.law.uw.edu/casestrainer/

### Development Setup
```powershell
# Start development environment
.\launcher.ps1 -Environment DockerDevelopment

# Or manual development setup
docker-compose -f docker-compose.yml up -d
```

## 🔍 Troubleshooting

### Common Issues
- **404 Errors**: Check container status and rebuild frontend
- **500 Errors**: Check Redis connection and backend logs
- **Assets Not Loading**: Verify Nginx asset routing configuration
- **Parallel Citations Missing**: Rebuild frontend and backend containers

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

### Logs
```powershell
# Backend logs
docker logs casestrainer-backend-prod

# Frontend logs
docker logs casestrainer-frontend-prod

# Nginx logs
docker logs casestrainer-nginx-prod

# Redis logs
docker logs casestrainer-redis-prod
```

For detailed troubleshooting, see [TROUBLESHOOTING.md](deployment/TROUBLESHOOTING.md).

## 📚 Documentation

- [Deployment Guide](deployment/DEPLOYMENT.md) - Complete deployment instructions
- [Troubleshooting Guide](deployment/TROUBLESHOOTING.md) - Common issues and solutions
- [API Documentation](docs/API_DOCUMENTATION.md) - Backend API reference
- [Changelog](CHANGELOG.md) - Version history and changes

## 🔄 Recent Updates (v1.2.0)

### Fixed Issues
- **Parallel Citations**: Fixed frontend display of parallel citations
- **Case Name Extraction**: Enhanced case name and date extraction logic
- **Asset Loading**: Fixed 404 errors for frontend assets
- **Container Networking**: Fixed frontend container startup issues

### Improvements
- **Documentation**: Comprehensive troubleshooting and deployment guides
- **Backend Processing**: Improved citation processing pipeline
- **Error Handling**: Better error handling and logging throughout

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in Docker environment
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the [troubleshooting guide](deployment/TROUBLESHOOTING.md)
2. Review the [deployment documentation](deployment/DEPLOYMENT.md)
3. Contact the system administrator with specific error messages and logs

---

**CaseStrainer v1.2.0** - Production-ready legal citation analysis system 