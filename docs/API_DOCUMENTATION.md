# CaseStrainer API Documentation

## ⚠️ **IMPORTANT: Canonical vs Deprecated Endpoints**

**Canonical Endpoints (Use These):**
- `POST /casestrainer/api/analyze` - Main endpoint for all document analysis
- `GET /casestrainer/api/health` - Health check
- `GET /casestrainer/api/version` - Version information
- `GET /casestrainer/api/task_status/<task_id>` - Task status
- `GET /casestrainer/api/server_stats` - Server statistics
- `GET /casestrainer/api/db_stats` - Database statistics

**Deprecated Endpoints (Do NOT Use):**
- `POST /casestrainer/api/process-text` - Deprecated, forwards to `/analyze`
- `POST /casestrainer/api/analyze-document` - Deprecated, forwards to `/analyze`
- All endpoints in `docker/src/deprecated_verifiers/` - Completely disabled

## Overview
CaseStrainer provides a comprehensive API for legal citation verification and analysis. The system uses the enhanced `EnhancedMultiSourceVerifier` with CourtListener API integration, volume range validation, format analysis, and likelihood scoring.

## Core Features

### ✅ **Enhanced Citation Verification**
- **Primary Source**: CourtListener API (fast, reliable)
- **Washington Normalization**: `Wn.` → `Wash.` (e.g., `149 Wn.2d 647` → `149 Wash. 2d 647`)
- **Volume Range Validation**: Comprehensive validation for all reporter series
- **Format Analysis**: Detailed regex-based pattern matching
- **Likelihood Scoring**: Sophisticated scoring for real vs. fictional citations
- **Enhanced Error Explanations**: Clear, actionable feedback

### ✅ **Performance Features**
- **Caching**: 1-hour TTL for API responses
- **Rate Limiting**: Built-in retry logic and rate limiting
- **Connection Pooling**: Efficient HTTP connection management
- **Performance Tracking**: Detailed timing and statistics

### ✅ **Case Name Extraction**
- **Context Extraction**: Extract case names from surrounding text
- **Hinted Extraction**: Use canonical names to find context-specific mentions
- **Date Extraction**: Extract dates from citation strings

## ✅ **Canonical API Endpoints**

### POST `/casestrainer/api/analyze`

**Main endpoint for all document analysis** - This is the only endpoint you should use for citation verification and document analysis.

#### Request
```json
{
  "text": "The court held in State v. Rohrich, 149 Wn.2d 647, that...",
  "source_type": "text"
}
```

#### Response
```json
{
  "citations": [
    {
      "citation": "149 Wn.2d 647",
      "canonical_citation": "149 Wash. 2d 647",
      "case_name": "State v. Rohrich",
      "canonical_name": "State v. Rohrich",
      "extracted_case_name": "State v. Rohrich",
      "hinted_case_name": "State v. Rohrich",
      "extracted_date": "2003",
      "canonical_date": "2003-06-26",
      "url": "https://www.courtlistener.com/opinion/4907935/state-v-rohrich/",
      "court": "Supreme Court of Washington",
      "docket_number": "71447-1",
      "verified": true,
      "valid": true,
      "confidence": 0.95,
      "source": "courtlistener",
      "format_analysis": {
        "format_type": "state_reporter",
        "is_valid_format": true,
        "is_valid_volume": true,
        "details": {
          "volume": 149,
          "page": 647,
          "valid_volume_range": "1-1000"
        }
      },
      "likelihood_score": 0.8,
      "explanation": "Citation format is valid and has characteristics of a real case.",
      "metadata": {
        "processing_time": 1.2,
        "source_name": "single_citation",
        "source_type": "citation",
        "timestamp": "2025-06-27T04:05:23.408815Z"
      }
    }
  ],
  "status": "success"
}
```

#### Error Response (Invalid Citation)
```json
{
  "citations": [
    {
      "citation": "999 F.999d 999 (2025)",
      "canonical_citation": "999 F.999d 999 (2025)",
      "verified": false,
      "valid": false,
      "confidence": 0.1,
      "source": "enhanced_verifier",
      "format_analysis": {
        "format_type": "federal_reporter",
        "is_valid_format": true,
        "is_valid_volume": false,
        "volume_error": "Volume 999 is outside the valid range (1-1500) for federal_reporter series 999"
      },
      "likelihood_score": 0.2,
      "explanation": "Invalid volume number: Volume 999 is outside the valid range (1-1500) for federal_reporter series 999",
      "error": "Invalid volume number: Volume 999 is outside the valid range (1-1500) for federal_reporter series 999"
    }
  ],
  "status": "success"
}
```

## ❌ **Deprecated Endpoints (Do NOT Use)**

The following endpoints are deprecated and should not be used in new code:

- `POST /casestrainer/api/process-text` - Deprecated, forwards to `/analyze`
- `POST /casestrainer/api/analyze-document` - Deprecated, forwards to `/analyze`
- All endpoints in `docker/src/deprecated_verifiers/` - Completely disabled

**Warning**: These deprecated endpoints will be removed in future versions.

## Enhanced Features

### **Volume Range Validation**
The system validates citation volumes against expected ranges:

- **U.S. Reports**: 1-1000
- **Federal Reporter F.1d**: 1-500
- **Federal Reporter F.2d**: 1-1500
- **Federal Reporter F.3d**: 1-1500
- **Federal Supplement**: 1-1500
- **Supreme Court Reporter**: 1-1000

### **Citation Format Analysis**
Comprehensive pattern matching for:
- U.S. Reports (`410 U.S. 113 (1973)`)
- Federal Reporter (`123 F.3d 456 (9th Cir. 1997)`)
- Federal Supplement (`456 F.Supp.2d 789 (D. Mass. 2006)`)
- State Reporters (`149 Wash. 2d 647 (2003)`)
- Regional Reporters (`456 N.E.2d 789 (Ill. 1983)`)
- Supreme Court Reporter (`93 S.Ct. 705 (1973)`)
- Lawyers Edition (`93 L.Ed.2d 705 (1973)`)
- Westlaw (`2024 WL 123456`)

### **Likelihood Scoring**
Scores citations from 0.0 to 1.0 based on:
- Format validity
- Volume range validity
- Citation type (U.S. Reports vs. state reporters)
- Case name presence
- Historical patterns

### **Enhanced Error Explanations**
Provides detailed feedback:
- **Invalid Format**: "Unrecognized citation format"
- **Invalid Volume**: "Volume 999 is outside the valid range"
- **Likely Hallucination**: "Citation format is valid but likely a hallucination"
- **Possible Real Case**: "Citation format is valid and has characteristics of a real case"

## Usage Examples

### **Valid Citation**
```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "410 U.S. 113 (1973)"}'
```

### **Invalid Citation**
```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "999 F.999d 999 (2025)"}'
```

### **Washington Citation**
```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "149 Wn.2d 647"}'
```

### **Text with Multiple Citations**
```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The court held in State v. Rohrich, 149 Wn.2d 647, and Roe v. Wade, 410 U.S. 113 (1973), that..."}'
```

## Response Fields

### **Core Fields**
- `citation`: Original citation text
- `canonical_citation`: Normalized citation (e.g., `Wn.` → `Wash.`)
- `verified`: Whether citation was verified in CourtListener
- `valid`: Whether citation format is valid
- `confidence`: Confidence score (0.0-1.0)

### **Case Information**
- `case_name`: Extracted case name
- `canonical_name`: Canonical case name from CourtListener
- `extracted_case_name`: Case name extracted from context
- `hinted_case_name`: Case name found using canonical name hints

### **Date Information**
- `extracted_date`: Date extracted from citation
- `canonical_date`: Canonical date from CourtListener

### **Enhanced Analysis**
- `