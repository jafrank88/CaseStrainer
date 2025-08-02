# CaseStrainer API Documentation (Updated)

## ⚠️ **IMPORTANT: Upload Behavior**

**CaseStrainer processes each request independently** to ensure fresh, accurate results and maintain privacy. Each file upload, URL submission, or text input is processed as a new request.

## Core Endpoints

### 1. Health Check
```
GET /casestrainer/api/health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-07-31T20:36:24-07:00"
}
```

### 2. Start Analysis
```
POST /casestrainer/api/analyze
```
**Supported Input Types:**
1. **File Upload** (multipart/form-data)
2. **Direct Text** (application/json)
3. **URL** (via 'url' parameter in JSON)

**Request Headers:**
```
Content-Type: multipart/form-data  # For file upload
Content-Type: application/json     # For text/URL
```

**File Upload Example:**
```bash
curl -X POST \
  'http://localhost:5000/casestrainer/api/analyze' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@document.pdf;type=application/pdf'
```

**Text Analysis Example:**
```bash
curl -X POST \
  'http://localhost:5000/casestrainer/api/analyze' \
  -H 'Content-Type: application/json' \
  -d '{"text": "This is a legal document citing 171 Wash. 2d 486"}'
```

**URL Analysis Example:**
```bash
curl -X POST \
  'http://localhost:5000/casestrainer/api/analyze' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/legal-document"}'
```

**Response (202 Accepted):**
```json
{
  "status": "started",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Analysis started"
}
```

### 3. Check Analysis Progress
```
GET /casestrainer/api/analyze/progress/<task_id>
```

**Response (200 OK):**
```json
{
  "status": "processing",
  "progress": 45,
  "message": "Processing document..."
}
```

### 4. Get Analysis Results
```
GET /casestrainer/api/analyze/results/<task_id>
```

**Response (200 OK):**
```json
{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "citation": "171 Wash. 2d 486",
      "valid": true,
      "case_name": "State v. Smith",
      "year": 2011,
      "reporter": "Wash.",
      "volume": 171,
      "page": 486,
      "series": 2,
      "jurisdiction": "washington",
      "confidence": 0.98
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input",
  "message": "No valid input provided. Please provide a file, text, or URL."
}
```

### 404 Not Found
```json
{
  "error": "Task not found",
  "message": "The specified task ID does not exist or has expired."
}
```

### 500 Internal Server Error
```json
{
  "error": "Processing error",
  "message": "An error occurred while processing your request."
}
```

## Best Practices

1. **Always check the task status** before attempting to fetch results
2. **Handle timeouts** - Long documents may take several minutes to process
3. **Cache results** on the client side when possible to avoid reprocessing
4. **Implement retry logic** for transient failures
5. **Respect rate limits** - Avoid sending too many requests in a short period

## Rate Limiting

- **Default Limit**: 60 requests per minute per IP address
- **Response Headers**:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets (UTC timestamp)

## Versioning

API versioning is handled through the URL path. The current version is `v1`:
```
/casestrainer/api/v1/...
```

## Authentication

Currently, no authentication is required for the public API endpoints. However, this may change in future versions.

## Support

For questions or issues, please contact [support email] or open an issue in our [GitHub repository].
