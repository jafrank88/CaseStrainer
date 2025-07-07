# CaseStrainer Changelog

All notable changes to CaseStrainer will be documented in this file.

## [1.2.0] - 2024-12-30

### Fixed
- **Parallel Citations Display**: Fixed frontend not displaying parallel citations from backend `parallels` arrays
  - Updated `CitationResults.vue` to process `parallels` arrays within citation objects
  - Added logic to handle parallel citations with `is_parallel_citation: true`
  - Parallel citations now appear as tags below primary citations
- **Case Name and Date Extraction**: Fixed backend not using enhanced extraction logic
  - Replaced `ComplexCitationIntegrator` with proper `CitationExtractor` and `EnhancedMultiSourceVerifier`
  - Added proper parameters for `extracted_case_name` and `extracted_date` in verification calls
  - Enhanced extraction now properly populates `extracted_case_name`, `extracted_date`, and `hinted_case_name` fields
- **Frontend Asset Loading**: Fixed 404 errors for frontend assets (JS/CSS files)
  - Added proper `/assets/` routing in Nginx configuration
  - Fixed asset base paths in Vue build configuration
- **Container Networking**: Fixed frontend container wait script
  - Updated `wait-for-backend.sh` to use correct backend container name `casestrainer-backend-prod`
  - Fixed infinite loop in frontend container startup

### Changed
- **Documentation**: Updated deployment and troubleshooting guides
  - Added comprehensive troubleshooting section for common issues
  - Documented Docker production setup and container management
  - Added diagnostic commands and health check procedures
- **Backend Processing**: Improved citation processing pipeline
  - Enhanced case name and date extraction with better context handling
  - Improved parallel citation detection and processing
  - Better error handling and logging throughout the pipeline

### Technical Details
- **Files Modified**:
  - `casestrainer-vue-new/src/components/CitationResults.vue` - Parallel citations processing
  - `src/document_processing.py` - Enhanced extraction logic
  - `nginx/conf.d/ssl.conf` - Asset routing configuration
  - `casestrainer-vue-new/wait-for-backend.sh` - Container networking fix
  - `deployment/DEPLOYMENT.md` - Updated deployment documentation
  - `deployment/TROUBLESHOOTING.md` - Comprehensive troubleshooting guide

## [1.1.0] - 2024-12-29

### Added
- **Docker Production Setup**: Complete Docker-based production deployment
  - Multi-container architecture with Nginx, Frontend, Backend, Redis, and RQ Workers
  - SSL termination and reverse proxy configuration
  - Health checks and resource limits for production stability
- **Async Task Processing**: Redis-based task queue for citation processing
  - RQ (Redis Queue) integration for background task processing
  - Progress tracking and ETA estimation for large documents
  - Improved response times for long-running operations
- **Enhanced Citation Verification**: Improved citation analysis capabilities
  - CourtListener API integration for citation verification
  - Parallel citation detection and processing
  - Complex citation handling with multiple components

### Changed
- **Architecture**: Migrated from single-process to containerized microservices
  - Frontend served by Nginx container
  - Backend API with Waitress WSGI server
  - Redis for caching and task queuing
  - Multiple RQ workers for parallel processing

## [1.0.0] - 2024-12-28

### Added
- **Initial Release**: Basic citation extraction and verification
- **Vue.js Frontend**: Modern web interface for document analysis
- **Flask Backend**: Python API for citation processing
- **File Upload Support**: PDF, DOCX, RTF, and text file processing
- **Citation Verification**: Basic verification against legal databases

---

## Versioning

This project uses [Semantic Versioning](http://semver.org/). For the versions available, see the tags on this repository.

## Release Process

1. **Development**: Features and fixes are developed in feature branches
2. **Testing**: All changes are tested in Docker production environment
3. **Documentation**: Changelog and documentation are updated
4. **Release**: Version is tagged and deployed to production
5. **Monitoring**: System health and performance are monitored post-release 