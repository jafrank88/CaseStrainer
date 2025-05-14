# CaseStrainer API Documentation

This document provides comprehensive documentation for all API endpoints in the CaseStrainer application.

## Base URL

- Development: `http://localhost:5000/api`
- Production: `https://wolf.law.uw.edu/casestrainer/api`

## Authentication

Most endpoints require a valid API key to be included in the request header:

```http
Authorization: Bearer your_api_key_here
```

## Endpoints

### 1. Citation Analysis

#### Analyze Brief Text
```http
POST /analyze
```

Analyzes a brief's text for citations and verifies them.

**Request Body:**
```json
{
  "text": "The brief text content here...",
  "api_key": "your_courtlistener_api_key"
}
```

**Response:**
```json
{
  "success": true,
  "citations": [
    {
      "citation_text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
      "case_name": "Brown v. Board of Education",
      "confidence": 0.95,
      "verified": true,
      "source": "CourtListener API"
    }
  ],
  "unconfirmed_citations": [
    {
      "citation_text": "Smith v. Jones, 123 F.3d 456 (2020)",
      "confidence": 0.3,
      "explanation": "Citation not found in any database"
    }
  ]
}
```

### 2. Citation Verification

#### Verify Single Citation
```http
POST /verify_citation
```

Verifies a single citation using multiple sources.

**Request Body:**
```json
{
  "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
  "case_name": "Brown v. Board of Education"
}
```

**Response:**
```json
{
  "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
  "case_name": "Brown v. Board of Education",
  "is_valid": true,
  "confidence": 0.9,
  "explanation": "Citation verified with Court Listener API",
  "source": "CourtListener API",
  "url": "https://www.courtlistener.com/opinion/..."
}
```

### 3. Unconfirmed Citations

#### Get Unconfirmed Citations
```http
GET /unconfirmed_citations_data
```

Retrieves all unconfirmed citations from the database.

**Response:**
```json
{
  "citations": [
    {
      "citation_text": "Smith v. Jones, 123 F.3d 456 (2020)",
      "case_name": "Unknown",
      "confidence": 0.3,
      "explanation": "No explanation available",
      "document": "brief_2023_01.pdf"
    }
  ]
}
```

### 4. Multitool Confirmed Citations

#### Get Multitool Confirmed Citations
```http
GET /confirmed_with_multitool_data
```

Retrieves citations that were confirmed using multiple verification tools.

**Response:**
```json
{
  "citations": [
    {
      "citation_text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
      "case_name": "Brown v. Board of Education",
      "confidence": 0.95,
      "source": "Multiple Sources",
      "url": "https://www.courtlistener.com/opinion/...",
      "explanation": "Verified by CourtListener and LangSearch"
    }
  ]
}
```

### 5. Citation Network

#### Get Citation Network Data
```http
GET /citation_network_data
```

Retrieves data for the citation network visualization.

**Response:**
```json
{
  "nodes": [
    {
      "id": "citation1",
      "label": "Brown v. Board of Education",
      "group": "landmark"
    }
  ],
  "edges": [
    {
      "from": "citation1",
      "to": "citation2",
      "label": "cited by"
    }
  ]
}
```

### 6. Enhanced Citation Validation

#### Enhanced Citation Validation
```http
POST /enhanced-validate-citation
```

Uses the enhanced validator to verify a citation with additional context and ML analysis.

**Request Body:**
```json
{
  "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)"
}
```

**Response:**
```json
{
  "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
  "verified": true,
  "confidence": 0.98,
  "context": {
    "surrounding_text": "...",
    "related_citations": [...],
    "full_text_url": "..."
  },
  "ml_analysis": {
    "confidence_score": 0.98,
    "explanation": "Citation matches known pattern and context",
    "similar_citations": [...]
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "message": "Detailed error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "Detailed error message"
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. The current limits are:

- 100 requests per minute per API key
- 1000 requests per hour per API key

When rate limits are exceeded, the API will return a 429 Too Many Requests response:

```json
{
  "error": "Rate limit exceeded",
  "message": "Please try again in X seconds",
  "retry_after": 60
}
```

## Best Practices

1. Always include proper error handling in your API calls
2. Cache responses when appropriate to reduce API load
3. Use the enhanced validator for critical citations
4. Implement exponential backoff for retries
5. Monitor your API usage to stay within rate limits 