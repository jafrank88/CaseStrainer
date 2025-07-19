# CaseStrainer API Documentation

## ⚠️ **IMPORTANT: Upload Behavior Warning**

**CaseTrainer does NOT cache or deduplicate uploads.** Each file upload, URL submission, or text input is processed as a completely new request. This means:

- **Files are always re-uploaded** - No duplicate detection
- **URLs are always re-processed** - Fresh web scraping each time  
- **Text is always re-analyzed** - No caching of results

**This is by design** to ensure fresh, accurate results and maintain privacy. See [Upload Behavior Warning](UPLOAD_BEHAVIOR_WARNING.md) for details and best practices.

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

CaseStrainer provides a comprehensive API for legal citation verification and analysis. The system uses the enhanced `UnifiedCitationProcessorV2` with CourtListener API integration, citation variant testing, context-aware case name extraction, and intelligent clustering.

## Core Features

### ✅ **Enhanced Citation Verification**

- **Primary Source**: CourtListener API (fast, reliable)
- **Citation Variants**: Automatic testing of multiple citation formats (e.g., `171 Wash. 2d 486`, `171 Wn.2d 486`, `171 Wn. 2d 486`)
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

- **Context Extraction**: Extract case names from surrounding text using bracketed context windows
- **Canonical Name Trimming**: Use canonical names to trim extracted case names intelligently
- **Date Extraction**: Extract dates from citation strings and context

### ✅ **Citation Clustering**

- **Parallel Citation Detection**: Group related citations to avoid duplication
- **Intelligent Clustering**: Citations close together with same case name and year are grouped
- **Priority System**: Clusters take priority over individual citations

## ✅ **Canonical API Endpoints**

### POST `/casestrainer/api/analyze`

**Main endpoint for all document analysis** - This is the primary endpoint for citation verification and document analysis with async processing.

### POST `/casestrainer/api/analyze_enhanced`

**Enhanced synchronous endpoint** - Provides immediate results for text analysis without file upload support. Best for quick testing and simple text processing.

#### Request

```json
{
  "text": "The court held in State v. Rohrich, 149 Wn.2d 647, that...",
  "source_type": "text"
}

```text

#### Response (Async Processing)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Document analysis started"
}

```text

#### Final Response (After Processing)

```json
{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
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
      "source": "CourtListener (Citation-Lookup) - variant: 149 Wash. 2d 647",
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
  "citations": [...],
  "clusters": [
    {
      "cluster_id": "cluster_1",
      "canonical_name": "State v. Rohrich",
      "canonical_date": "2003",
      "extracted_case_name": "State v. Rohrich",
      "extracted_date": "2003",
      "citations": [...],
      "size": 2
    }
  ],
  "case_names": [...],
  "metadata": {
    "processing_time": 5.2,
    "total_citations": 15,
    "verified_citations": 12,
    "clusters_found": 8
  },
  "statistics": {
    "total_citations": 15,
    "verified_count": 12,
    "unverified_count": 3,
    "average_confidence": 0.87
  },
  "summary": {
    "document_type": "legal_brief",
    "primary_jurisdiction": "Washington",
    "citation_strength": "strong"
  }
}

```text

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

```text

### POST `/casestrainer/api/analyze_enhanced` (2)

**Enhanced synchronous endpoint** for immediate text analysis without file upload support.

#### Request Format

```json
{
  "type": "text",
  "text": "The court held in State v. Rohrich, 149 Wn.2d 647, that..."
}

```text

#### Response Format (Immediate)

```json
{
  "citations": [
    {
      "citation": "149 Wn.2d 647",
      "case_name": "State v. Rohrich",
      "extracted_case_name": "State v. Rohrich",
      "canonical_name": "State v. Rohrich",
      "extracted_date": "2003",
      "canonical_date": "2003",
      "verified": true,
      "court": "Supreme Court of Washington",
      "confidence": 0.95,
      "method": "CourtListener",
      "url": "https://www.courtlistener.com/opinion/12345/",
      "source": "CourtListener",
      "metadata": {
        "processing_time": 1.2,
        "timestamp": "2025-06-27T04:05:23.408815Z"
      }
    }
  ],
  "clusters": [
    {
      "cluster_id": "cluster_1",
      "canonical_name": "State v. Rohrich",
      "canonical_date": "2003",
      "extracted_case_name": "State v. Rohrich",
      "extracted_date": "2003",
      "citations": [...],
      "size": 2
    }
  ],
  "success": true
}

```text

#### Limitations

- **No file uploads** - Returns 501 "Not Implemented" error
- **No URL processing** - Text input only
- **No progress tracking** - Immediate results only
- **No task IDs** - Direct response format

#### Use Cases

- **Quick testing** of citation extraction
- **Simple text analysis** without file processing
- **Development and debugging** of citation logic
- **Lightweight integration** where async processing isn't needed

## ❌ **Deprecated Endpoints (Do NOT Use)**

The following endpoints are deprecated and should not be used in new code:

- `POST /casestrainer/api/process-text` - Deprecated, forwards to `/analyze`
- `POST /casestrainer/api/analyze-document` - Deprecated, forwards to `/analyze`
- All endpoints in `docker/src/deprecated_verifiers/` - Completely disabled

**Warning**: These deprecated endpoints will be removed in future versions.

## Enhanced Features

### **Citation Variant Testing**

The system automatically generates and tests multiple citation formats to improve hit rates:

- **Washington Citations**: `171 Wash. 2d 486`, `171 Wn.2d 486`, `171 Wn. 2d 486`, `171 Washington 2d 486`
- **Federal Citations**: `410 U.S. 113`, `410 US 113`, `410 United States 113`
- **Regional Citations**: `456 P.3d 789`, `456 P.3d 789`, `456 Pacific 3d 789`

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

```text

### **Invalid Citation**

```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "999 F.999d 999 (2025)"}'

```text

### **Washington Citation**

```bash
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "149 Wn.2d 647 (2003)"}'

```text

## Processing Pipeline

### **1. Citation Extraction**

- **Regex Extraction**: Primary extraction using comprehensive patterns
- **Eyecite Extraction**: Secondary extraction using eyecite library (if available)
- **Context Analysis**: Extract case names and dates from surrounding text

### **2. Citation Normalization**

- **Washington Normalization**: Convert `Wn.` to `Wash.` formats
- **Format Standardization**: Standardize spacing and punctuation
- **Variant Generation**: Generate multiple citation formats for testing

### **3. Citation Verification**

- **CourtListener API**: Primary verification using citation-lookup endpoint
- **Search API Fallback**: Secondary verification using search endpoint
- **Web Search Fallback**: Tertiary verification using web search (if enabled)

### **4. Citation Clustering**

- **Parallel Detection**: Group citations that appear together
- **Deduplication**: Remove duplicate citations
- **Priority Assignment**: Assign priority to clusters over individual citations

### **5. Result Enhancement**

- **Canonical Data**: Add canonical names, dates, and URLs
- **Confidence Scoring**: Calculate confidence scores
- **Metadata Addition**: Add processing metadata and timing information

## Error Handling

The API includes comprehensive error handling:

- **Graceful Degradation**: Falls back to basic processing if enhanced features fail
- **Detailed Logging**: Comprehensive logging for debugging
- **Validation Errors**: Clear error messages for validation failures
- **Timeout Handling**: Proper timeout handling for external API calls

## Performance Considerations

- **Async Processing**: Citation processing uses async/await for better performance
- **Thread Pool**: CPU-intensive operations use thread pools
- **Caching**: Intelligent caching of validation results
- **Batch Processing**: Efficient batch processing of multiple citations

## Migration from Legacy System

The enhanced system maintains backward compatibility:

- **Legacy Endpoints**: Existing `/api/analyze` endpoint continues to work
- **Response Format**: Enhanced responses maintain compatibility with existing frontend
- **Gradual Migration**: Can be enabled/disabled per endpoint
- **Fallback Support**: Falls back to legacy processing if enhanced system fails
