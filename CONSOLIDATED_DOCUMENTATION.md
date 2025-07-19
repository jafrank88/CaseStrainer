# CaseStrainer - Comprehensive Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Security](#security)
4. [Deployment](#deployment)
5. [Development](#development)
6. [Performance](#performance)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Changelog](#changelog)
10. [Contributing](#contributing)

---

## Project Overview

CaseStrainer is a comprehensive legal citation extraction and verification system designed to process legal documents and extract case citations with high accuracy. The system provides both API endpoints and a web interface for document processing.

### Key Features

- **Citation Extraction**: Advanced pattern matching and ML-based extraction
- **Citation Verification**: Integration with CourtListener API and web search
- **Document Processing**: Support for PDF, DOCX, and text files
- **Web Interface**: Vue.js frontend with real-time processing
- **API Access**: RESTful API for integration with other systems
- **Security**: Comprehensive security measures and input validation

### Technology Stack

- **Backend**: Python Flask with Redis for task queuing
- **Frontend**: Vue.js 3 with Vite
- **Database**: SQLite for caching and metadata
- **Containerization**: Docker with Nginx reverse proxy
- **Security**: Bandit security scanning, input validation, rate limiting

---

## Architecture

### System Components

#### Backend Services

- **Flask Application** (`src/app_final_vue.py`): Main web server
- **Citation Processor** (`src/unified_citation_processor.py`): Core citation extraction
- **API Endpoints** (`src/vue_api_endpoints.py`): REST API implementation
- **Cache Manager** (`src/cache_manager.py`): Redis and SQLite caching
- **Progress Manager** (`src/progress_manager.py`): Async task tracking

#### Frontend Components

- **Vue.js Application**: Modern reactive interface
- **Citation Results**: Real-time display of extraction results
- **File Upload**: Drag-and-drop document processing
- **Progress Tracking**: Visual feedback for long-running tasks

#### Infrastructure

- **Docker**: Containerized deployment
- **Nginx**: Reverse proxy and SSL termination
- **Redis**: Task queue and caching
- **SQLite**: Local metadata storage

### Data Flow

1. **Document Upload**: Files uploaded via web interface or API
2. **Text Extraction**: PDF/DOCX converted to text using multiple methods
3. **Citation Extraction**: Pattern matching and ML-based extraction
4. **Verification**: CourtListener API lookup and web search fallback
5. **Result Display**: Formatted results with confidence scores

---

## Security

### Security Measures Implemented

#### Input Validation

- **File Type Validation**: Strict MIME type checking
- **Size Limits**: Configurable file size restrictions
- **Content Sanitization**: HTML/script injection prevention
- **Rate Limiting**: API request throttling

#### API Security

- **Authentication**: API key validation for external access
- **CORS Configuration**: Proper cross-origin request handling
- **Request Validation**: Comprehensive input sanitization
- **Error Handling**: Secure error messages without information leakage

#### Infrastructure Security

- **SSL/TLS**: HTTPS enforcement with proper certificate handling
- **Container Security**: Non-root user execution
- **Network Security**: Firewall rules and port restrictions
- **Secret Management**: Environment variable configuration

### Security Testing

- **Bandit Scanning**: Automated security vulnerability detection
- **Manual Review**: Regular code security audits
- **Dependency Scanning**: Known vulnerability checking
- **Penetration Testing**: Periodic security assessments

### Security Checklist

- [x] Input validation on all endpoints
- [x] File upload security measures
- [x] API authentication and authorization
- [x] SQL injection prevention
- [x] XSS protection
- [x] CSRF protection
- [x] Rate limiting implementation
- [x] Secure error handling
- [x] SSL/TLS configuration
- [x] Security headers implementation

---

## Deployment

### Production Deployment

#### Prerequisites

- Docker and Docker Compose
- SSL certificates
- Domain configuration
- Server with minimum 4GB RAM

#### Deployment Steps

1. **Clone Repository**: `git clone <repository-url>`
2. **Configure Environment**: Set up `.env` and `.env.production`
3. **SSL Setup**: Configure certificates in `nginx/ssl/`
4. **Build Images**: `docker-compose -f docker-compose.prod.yml build`
5. **Start Services**: `docker-compose -f docker-compose.prod.yml up -d`
6. **Verify Deployment**: Check health endpoints and logs

#### Configuration Files

- **Docker Compose**: `docker-compose.prod.yml`
- **Nginx Configuration**: `nginx/conf/casestrainer.conf`
- **Environment Variables**: `.env.production`
- **SSL Certificates**: `nginx/ssl/`

### Development Setup

1. **Python Environment**: `python -m venv venv`
2. **Dependencies**: `pip install -r requirements.txt`
3. **Redis**: Start Redis server locally
4. **Frontend**: `cd casestrainer-vue-new && npm install && npm run dev`
5. **Backend**: `python src/app_final_vue.py`

### Monitoring and Logging

- **Application Logs**: `logs/casestrainer.log`
- **Nginx Logs**: `nginx/logs/`
- **Docker Logs**: `docker logs <container-name>`
- **Health Checks**: `/health` endpoint monitoring

---

## Development

### Code Organization

#### Source Structure

```text

src/
├── app_final_vue.py              # Main Flask application
├── vue_api_endpoints.py          # API endpoint definitions
├── unified_citation_processor.py # Core citation processing
├── citation_extractor.py         # Citation extraction logic
├── cache_manager.py              # Caching layer
├── progress_manager.py           # Async task management
└── utils/                        # Utility functions

```text

#### Configuration Management

- **Development**: `config/config_dev.py`
- **Production**: `config/config_prod.py`
- **Environment Variables**: `.env` files
- **Docker Configuration**: `docker-compose.yml`

### Development Workflow

1. **Feature Development**: Create feature branches
2. **Testing**: Run comprehensive test suite
3. **Code Review**: Security and quality review
4. **Integration**: Merge to main branch
5. **Deployment**: Automated deployment pipeline

### Code Quality

- **Pylance**: Type checking and error detection
- **Bandit**: Security vulnerability scanning
- **Pytest**: Unit and integration testing
- **Code Formatting**: Black and isort
- **Linting**: Flake8 and pylint

---

## Performance

### Optimization Strategies

#### Backend Optimizations

- **Async Processing**: Redis-based task queuing
- **Caching**: Multi-layer caching (Redis + SQLite)
- **Connection Pooling**: Database connection optimization
- **Memory Management**: Efficient data structures

#### Frontend Optimizations

- **Code Splitting**: Lazy loading of components
- **Asset Optimization**: Minification and compression
- **Caching**: Browser and CDN caching
- **Bundle Analysis**: Webpack bundle optimization

#### Infrastructure Optimizations

- **Load Balancing**: Nginx load balancer configuration
- **Resource Limits**: Docker container resource constraints
- **Database Optimization**: Indexing and query optimization
- **CDN Integration**: Static asset delivery optimization

### Performance Monitoring

- **Response Times**: API endpoint performance tracking
- **Resource Usage**: CPU, memory, and disk monitoring
- **Error Rates**: Application error tracking
- **Throughput**: Request processing capacity

---

## Testing

### Test Strategy

#### Unit Testing

- **Citation Extraction**: Pattern matching accuracy
- **API Endpoints**: Request/response validation
- **Utility Functions**: Core functionality verification
- **Error Handling**: Exception and edge case testing

#### Integration Testing

- **End-to-End**: Complete workflow testing
- **API Integration**: External service integration
- **Database Operations**: Data persistence testing
- **File Processing**: Document upload and processing

#### Security Testing (2)

- **Vulnerability Scanning**: Automated security testing
- **Penetration Testing**: Manual security assessment
- **Input Validation**: Malicious input testing
- **Authentication**: Access control verification

### Test Execution

```bash

# Run all tests

python -m pytest tests/

# Run specific test categories

python -m pytest tests/test_api.py
python -m pytest tests/test_citation_verification.py

# Run with coverage

python -m pytest --cov=src tests/

```text

---

## Troubleshooting

### Common Issues

#### Application Issues

- **Startup Failures**: Check environment variables and dependencies
- **Memory Issues**: Monitor container resource usage
- **Database Errors**: Verify SQLite file permissions and integrity
- **API Failures**: Check external service connectivity

#### Deployment Issues

- **Container Failures**: Review Docker logs and health checks
- **SSL Problems**: Verify certificate configuration
- **Network Issues**: Check firewall and port configuration
- **Performance Issues**: Monitor resource usage and bottlenecks

#### Development Issues

- **Pylance Errors**: Fix type annotations and imports
- **Test Failures**: Update test data and mock configurations
- **Build Issues**: Check dependency versions and compatibility
- **Linting Errors**: Fix code style and formatting issues

### Debugging Tools

- **Log Analysis**: Structured logging with different levels
- **Health Checks**: Application and service health monitoring
- **Performance Profiling**: CPU and memory profiling tools
- **Network Debugging**: Request/response analysis

---

## Changelog

### Recent Updates

#### Version 2.0.0 (Current)

- **Major Refactoring**: Consolidated citation processing pipeline
- **Security Enhancements**: Comprehensive security audit and fixes
- **Performance Improvements**: Async processing and caching optimization
- **Documentation**: Complete documentation consolidation
- **Code Quality**: Pylance integration and type annotations

#### Version 1.5.0

- **Vue.js Migration**: Modern frontend framework implementation
- **API Enhancement**: RESTful API with comprehensive endpoints
- **Docker Support**: Containerized deployment configuration
- **SSL Integration**: HTTPS support with proper certificate handling

#### Version 1.0.0

- **Initial Release**: Core citation extraction functionality
- **Basic Web Interface**: Simple document upload and processing
- **CourtListener Integration**: Citation verification API
- **PDF Processing**: Document text extraction capabilities

### Future Roadmap

- **Machine Learning**: Enhanced citation extraction with ML models
- **Multi-language Support**: International legal document processing
- **Advanced Analytics**: Citation pattern analysis and reporting
- **API Marketplace**: Public API for third-party integrations

---

## Contributing

### Development Guidelines

1. **Code Style**: Follow PEP 8 and project formatting standards
2. **Testing**: Write comprehensive tests for new features
3. **Documentation**: Update documentation for API changes
4. **Security**: Follow security best practices
5. **Performance**: Consider performance impact of changes

### Pull Request Process

1. **Feature Branch**: Create feature branch from main
2. **Development**: Implement feature with tests
3. **Code Review**: Submit PR for review
4. **Testing**: Ensure all tests pass
5. **Merge**: Merge after approval and CI checks

---

*This documentation is automatically generated and consolidated from multiple source files. For the most up-to-date information, refer to the individual source files in the repository.*
