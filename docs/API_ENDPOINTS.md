# CaseStrainer API Endpoints

This document lists all active API endpoints in the CaseStrainer application after the cleanup of duplicate endpoints.

## Base URL
All API endpoints are prefixed with `/casestrainer/api/`

## Main Endpoints

### `/analyze` (POST)
**Unified endpoint for all document analysis**
- **Purpose**: Main endpoint for analyzing documents, text, and URLs
- **Input Types**: 
  - File upload (multipart/form-data)
  - Text input (JSON or form data)
  - URL input (JSON)
- **Features**:
  - PDF text extraction using pdfminer.six
  - Citation extraction and verification
  - Case name extraction
  - Canonical date extraction
  - Batch CourtListener verification
  - Async processing with progress tracking
- **Response**: JSON with citations, verification results, and metadata

### `/health` (GET)
**Health check endpoint**
- **Purpose**: Check if the API is running
- **Response**: JSON with status, environment, and version info

### `/version` (GET)
**Version information**
- **Purpose**: Get application version and build info
- **Response**: JSON with version details

### `/task_status/<task_id>` (GET)
**Task status endpoint**
- **Purpose**: Check status of async processing tasks
- **Parameters**: task_id (string)
- **Response**: JSON with task status and progress

### `/processing_progress` (GET)
**Processing progress endpoint**
- **Purpose**: Get overall processing progress
- **Response**: JSON with progress information

### `/server_stats` (GET)
**Server statistics**
- **Purpose**: Get server performance statistics
- **Response**: JSON with server stats

### `/db_stats` (GET)
**Database statistics**
- **Purpose**: Get database statistics and health
- **Response**: JSON with database stats

## Data Endpoints

### `/confirmed_with_multitool_data` (GET)
**Confirmed citations data**
- **Purpose**: Get citations confirmed by multi-source validation
- **Response**: JSON with confirmed citations data

### `/unconfirmed_citations_data` (GET)
**Unconfirmed citations data**
- **Purpose**: Get citations that could not be verified
- **Response**: JSON with unconfirmed citations data

### `/reprocess-citation` (POST)
**Reprocess citation**
- **Purpose**: Reprocess a specific citation with enhanced validation
- **Input**: JSON with citation text
- **Response**: JSON with reprocessing results

## Deprecated Endpoints (Forwarding)

### `/analyze-document` (POST) - DEPRECATED
- **Status**: Deprecated, forwards to `/analyze`
- **Purpose**: Legacy file upload endpoint
- **Note**: Use `/analyze` instead

### `/process-text` (POST) - DEPRECATED
- **Status**: Deprecated, forwards to `/analyze`
- **Purpose**: Legacy text processing endpoint
- **Note**: Use `/analyze` instead

## Frontend Routes

### `/casestrainer/` (GET)
**Main Vue.js application**
- **Purpose**: Serve the main Vue.js frontend
- **Features**: SPA fallback for all routes

### `/casestrainer/<path>` (GET)
**Static file serving**
- **Purpose**: Serve static assets for the Vue.js frontend
- **Features**: Proper caching headers and security

## Error Handling

All endpoints return consistent error responses:
- **400**: Bad Request (invalid input)
- **404**: Not Found (resource not found)
- **500**: Internal Server Error (server error)

Error responses include:
- `error`: Error message
- `message`: Additional context
- `status_code`: HTTP status code

## CORS Configuration

The API supports CORS with the following origins:
- `https://wolf.law.uw.edu`
- `http://localhost:5000`
- `http://localhost:8080`

## Authentication

Currently, no authentication is required for API endpoints.

## Rate Limiting

No rate limiting is currently implemented.

## File Upload Limits

- **Maximum file size**: 50MB
- **Supported formats**: PDF, DOC, DOCX, TXT, RTF, ODT, HTML, HTM
- **PDF extraction**: Uses pdfminer.six as primary extractor with fallbacks

## Notes

- All endpoints are prefixed with `/casestrainer/api/` when accessed through the main application
- The main `/analyze` endpoint handles all input types (file, text, URL) in a unified way
- Deprecated endpoints forward to the main `/analyze` endpoint for backward compatibility
- The application uses Redis and RQ for async task processing 