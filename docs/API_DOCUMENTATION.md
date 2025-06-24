# CaseStrainer API Documentation

This document provides comprehensive documentation for all API endpoints in the CaseStrainer application.

## Base URL

- Development: `http://localhost:5000/api`
- Production: `https://wolf.law.uw.edu/casestrainer/api`

## Multi-Source Citation Verification

CaseStrainer uses an **Enhanced Multi-Source Verification System** that checks citations against multiple legal databases and sources:

### Primary Sources
- **CourtListener API** (v4) - Primary legal database
- **Google Scholar** - Academic and legal research
- **Justia** - Legal information and case law
- **Leagle** - Legal research and case law
- **FindLaw** - Legal information and resources
- **CaseText** - Legal research platform

### Verification Process
1. **Database Check** - First checks local SQLite database for previously verified citations
2. **Multi-Source Verification** - If not found locally, queries multiple external sources
3. **Confidence Scoring** - Assigns confidence scores based on verification results
4. **Cache Storage** - Stores results for future use

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

Analyzes a brief's text for citations and verifies them using the multi-source verification system.

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
      "source": "Multiple Sources",
      "verification_details": {
        "courtlistener": true,
        "justia": true,
        "google_scholar": true
      }
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

#### Unified Citation Analysis
```http
POST /analyze
```

Analyzes citations from various input types (text, file, URL, or single citation) using the unified processing pipeline with enhanced multi-source verification.

**Request Body:**
```json
{
  "type": "text",
  "text": "Brown v. Board of Education, 347 U.S. 483 (1954)"
}
```

**For Single Citation (using text type):**
```json
{
  "type": "text", 
  "text": "181 Wash.2d 391, 333 P.3d 440"
}
```

**Response:**
```json
{
  "status": "success",
  "citations": [
    {
      "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
      "verified": true,
      "case_name": "Brown v. Board of Education",
      "case_name_extracted": "Brown v. Board of Education",
      "canonical_case_name": "Brown v. Board of Education",
      "confidence": 0.95,
      "source": "Multiple Sources",
      "sources": ["CourtListener", "Justia", "Google Scholar"],
      "url": "https://www.courtlistener.com/opinion/...",
      "verification_details": {
        "courtlistener": {
          "verified": true,
          "url": "https://www.courtlistener.com/opinion/..."
        },
        "justia": {
          "verified": true,
          "url": "https://supreme.justia.com/cases/federal/us/347/483/"
        },
        "google_scholar": {
          "verified": true
        }
      }
    }
  ],
  "metadata": {
    "total_citations": 1,
    "verified_count": 1,
    "processing_time": 2.5,
    "source_type": "text"
  }
}
```

**Note:** Single citations are processed through the same unified pipeline as multi-text analysis, ensuring consistent accuracy and performance optimizations.

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

Retrieves citations that were confirmed using the multi-source verification system.

**Response:**
```json
{
  "citations": [
    {
      "citation_text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
      "case_name": "Brown v. Board of Education",
      "confidence": 0.95,
      "source": "Multiple Sources",
      "verification_details": {
        "courtlistener": true,
        "justia": true,
        "google_scholar": true
      },
      "url": "https://www.courtlistener.com/opinion/...",
      "explanation": "Verified by multiple sources including CourtListener, Justia, and Google Scholar"
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

Uses the enhanced validator to verify a citation with additional context and ML analysis, leveraging the multi-source verification system.

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
  "source": "Enhanced Multi-Source Validator",
  "verification_details": {
    "pattern_recognition": true,
    "landmark_case": true,
    "ml_classification": true,
    "multi_source_verification": {
      "courtlistener": true,
      "justia": true,
      "google_scholar": true
    }
  },
  "context": {
    "surrounding_text": "...",
    "related_citations": [...],
    "case_summary": "Landmark case that declared racial segregation in public schools unconstitutional"
  }
}
```

### 7. Health Check

#### System Health
```http
GET /health
```

Returns the current health status of the API server and verification systems.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-23T13:04:42.251Z",
  "services": {
    "api_server": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "multi_source_verifier": "healthy"
  },
  "version": "2.0.0"
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "status_code": 400,
  "timestamp": "2025-06-23T13:04:42.251Z"
}
```

## Rate Limiting

- **Development**: No rate limiting
- **Production**: 100 requests per minute per IP address
- **Enhanced Validation**: 50 requests per minute per API key

## Caching

- **Citation Results**: Cached for 24 hours
- **Database Queries**: Cached for 1 hour
- **External API Calls**: Cached for 6 hours

## Performance

- **Average Response Time**: < 2 seconds
- **Multi-Source Verification**: < 5 seconds
- **Database Queries**: < 100ms
- **Cache Hit Rate**: > 80% 