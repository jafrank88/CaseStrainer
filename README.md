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
- **Enhanced Extraction**: Advanced case name and date extraction with context-aware processing
- **Citation Variants**: Automatic generation and testing of multiple citation formats (e.g., `171 Wash. 2d 486`, `171 Wn.2d 486`, `171 Wn. 2d 486`)
- **Parallel Citations**: Detection and display of parallel citations (e.g., "302 P.3d 156")
- **Verification**: CourtListener API integration with fallback to web search
- **Complex Citations**: Handling of complex citations with multiple components
- **Clustering**: Intelligent grouping of related citations to avoid duplication

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
- LangSearch API key (optional)

## 🔧 Configuration

### API Keys (Secure Setup)
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
- **LangSearch API Key**: For advanced text analysis (optional)

#### Security Best Practices
- ✅ Store keys as environment variables
- ✅ Never commit API keys to version control
- ✅ Use different keys for development and production
- ✅ Rotate keys regularly
- ❌ Don't store keys in config files
- ❌ Don't hardcode keys in source code

### Environment Variables
- `COURTLISTENER_API_KEY`: Your CourtListener API key
- `LANGSEARCH_API_KEY`: Your LangSearch API key (optional)
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
- **Citation Verification Failing**: Check CourtListener API key and network connectivity

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

For detailed troubleshooting, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 📚 Documentation

- [API Documentation](docs/API_DOCUMENTATION.md) - Backend API reference
- [Enhanced Citation Processing](docs/ENHANCED_CITATION_PROCESSING.md) - Citation processing details
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Deployment Guide](docs/DEPLOYMENT_VUE.md) - Complete deployment instructions

## 🔄 Recent Updates (v1.3.0)

### New Features
- **Citation Variant Verification**: System now tries multiple citation formats (e.g., `171 Wash. 2d 486`, `171 Wn.2d 486`, `171 Wn. 2d 486`) to improve hit rates
- **UnifiedCitationProcessorV2**: New unified processor with enhanced extraction and verification
- **Context-Aware Case Name Extraction**: Improved case name extraction using document context
- **Enhanced Clustering**: Better detection and grouping of parallel citations
- **Canonical Name Trimming**: Intelligent trimming of case names using canonical data

### Fixed Issues
- **Citation Verification**: Improved hit rates through variant testing
- **Case Name Extraction**: More accurate extraction with context awareness
- **Duplicate Citations**: Better deduplication and clustering logic
- **API Response**: Enhanced canonical metadata in API responses

### Improvements
- **Documentation**: Updated documentation to reflect current system state
- **Backend Processing**: Improved citation processing pipeline with multiple extraction methods
- **Error Handling**: Better error messages and fallback mechanisms 