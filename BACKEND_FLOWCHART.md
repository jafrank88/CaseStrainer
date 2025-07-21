# CaseStrainer Backend Function Flowchart

## Overview
This flowchart shows the backend function calls and data flow in CaseStrainer after the consolidation work. The system processes legal documents to extract, verify, and cluster citations.

## Main Application Flow

```mermaid
graph TD
    A[Client Request] --> B[Flask App: app_final_vue.py]
    B --> C{Request Type}
    
    C -->|GET /health| D[Health Check Endpoint]
    C -->|POST /analyze| E[Main Analyze Endpoint]
    C -->|POST /analyze_enhanced| F[Enhanced Analyze Endpoint]
    C -->|GET /task_status| G[Task Status Endpoint]
    
    D --> D1[Database Stats Check]
    D --> D2[Component Health Check]
    D1 --> D3[Return Health Status]
    D2 --> D3
    
    E --> E1{Input Type}
    E1 -->|File Upload| E2[File Upload Handler]
    E1 -->|JSON Text| E3[JSON Input Handler]
    E1 -->|Form Data| E4[Form Input Handler]
    
    F --> F1[Citation Service]
    F1 --> F2{Process Immediately?}
    F2 -->|Yes| F3[Immediate Processing]
    F2 -->|No| F4[Async Task Queue]
    
    G --> G1[Redis Queue Check]
    G1 --> G2[Return Task Status]
```

## Citation Processing Flow

```mermaid
graph TD
    A[Text Input] --> B[Citation Service]
    B --> C{Processing Strategy}
    
    C -->|Immediate| D[Direct Processing]
    C -->|Async| E[Redis Task Queue]
    
    D --> F[UnifiedCitationProcessorV2]
    E --> F
    
    F --> G[process_text Method]
    G --> H{Extraction Methods}
    
    H -->|Regex| I[Regex Extraction]
    H -->|Eyecite| J[Eyecite Extraction]
    
    I --> K[Citation Normalization]
    J --> K
    
    K --> L[Citation Deduplication]
    L --> M{Verification Enabled?}
    
    M -->|Yes| N[Citation Verification]
    M -->|No| O[Skip Verification]
    
    N --> P[CourtListener API]
    N --> Q[Web Search Fallback]
    
    O --> R[Result Formatting]
    P --> R
    Q --> R
    
    R --> S[Citation Clustering]
    S --> T[Return Results]
```

## File Processing Flow

```mermaid
graph TD
    A[File Upload] --> B[File Validation]
    B --> C[Generate Task ID]
    C --> D[Save to Uploads Directory]
    D --> E[Redis Task Queue]
    
    E --> F[Redis Worker]
    F --> G[DockerOptimizedProcessor]
    
    G --> H{File Size}
    H -->|Small < 10MB| I[Local Processing]
    H -->|Medium 10-100MB| J[Worker Queue]
    H -->|Large > 100MB| K[Distributed Processing]
    
    I --> L[PDF Text Extraction]
    J --> L
    K --> L
    
    L --> M{Extraction Method}
    M -->|Primary| N[pdfminer.six]
    M -->|Fallback| O[pypdf2]
    M -->|Last Resort| P[OCR]
    
    N --> Q[Text Cleaning]
    O --> Q
    P --> Q
    
    Q --> R[Citation Processing]
    R --> S[Return Results]
```

## Citation Verification Flow

```mermaid
graph TD
    A[Citation List] --> B[Group Citations]
    B --> C[Batch CourtListener API]
    
    C --> D{API Response}
    D -->|Success| E[Update Citation Data]
    D -->|Failure| F[Web Search Fallback]
    
    F --> G[ComprehensiveWebSearchEngine]
    G --> H{Search Sources}
    
    H -->|Primary| I[Justia, FindLaw]
    H -->|Secondary| J[Google Scholar, Bing]
    H -->|Tertiary| K[Other Legal Databases]
    
    I --> L[Result Validation]
    J --> L
    K --> L
    
    L --> M[Update Citation Status]
    E --> M
    
    M --> N[Citation Clustering]
    N --> O[Return Verified Citations]
```

## Consolidated Module Integration

```mermaid
graph TD
    A[Main Application] --> B[Consolidated Modules]
    
    B --> C[citation_utils_consolidated.py]
    B --> D[toa_utils_consolidated.py]
    B --> E[test_utilities_consolidated.py]
    
    C --> F[Citation Normalization]
    C --> G[Citation Formatting]
    C --> H[Citation Validation]
    
    D --> I[ToA Extraction]
    D --> J[ToA Comparison]
    D --> K[ToA Analysis]
    
    E --> L[Test Server]
    E --> M[Sample Citations]
    E --> N[Verification Tests]
    
    F --> O[UnifiedCitationProcessorV2]
    G --> O
    H --> O
    
    I --> P[Document Analysis]
    J --> P
    K --> P
    
    L --> Q[Development Testing]
    M --> Q
    N --> Q
```

## Data Flow Architecture

```mermaid
graph LR
    A[Client] --> B[Nginx Reverse Proxy]
    B --> C[Flask Application]
    
    C --> D[Vue API Endpoints]
    C --> E[Static File Serving]
    
    D --> F[Citation Service]
    D --> G[Task Management]
    D --> H[Database Manager]
    
    F --> I[UnifiedCitationProcessorV2]
    F --> J[Redis Distributed Processor]
    
    I --> K[Consolidated Utils]
    J --> K
    
    K --> L[CourtListener API]
    K --> M[Web Search Engines]
    K --> N[Local Database]
    
    G --> O[Redis Queue]
    G --> P[Task Status Tracking]
    
    H --> Q[SQLite Database]
    H --> R[Cache Management]
```

## Error Handling Flow

```mermaid
graph TD
    A[Request] --> B{Input Validation}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return 400 Error]
    
    C --> E{Processing}
    E -->|Success| F[Return Results]
    E -->|Failure| G[Error Handling]
    
    G --> H{Error Type}
    H -->|API Error| I[Retry with Fallback]
    H -->|File Error| J[Return File Error]
    H -->|System Error| K[Return 500 Error]
    
    I --> L[Web Search Fallback]
    L --> M{Success?}
    M -->|Yes| F
    M -->|No| K
    
    J --> N[Return 400 Error]
    K --> O[Log Error]
    O --> P[Return 500 Error]
```

## Key Function Calls

### Main Entry Points
1. **`app_final_vue.py`** - Flask application factory
2. **`vue_api_endpoints.py`** - API route handlers
3. **`citation_service.py`** - Business logic service

### Core Processing
1. **`UnifiedCitationProcessorV2.process_text()`** - Main citation processing
2. **`DockerOptimizedProcessor.process_document()`** - File processing
3. **`ComprehensiveWebSearchEngine.search_multiple_sources()`** - Web search

### Consolidated Utilities
1. **`citation_utils_consolidated.py`**:
   - `normalize_citation()` - Citation normalization
   - `generate_citation_variants()` - Citation variants
   - `apply_washington_spacing_rules()` - Formatting rules

2. **`toa_utils_consolidated.py`**:
   - `extract_toa_section()` - ToA extraction
   - `compare_citations()` - Citation comparison
   - `compare_toa_vs_analyze()` - ToA analysis

3. **`test_utilities_consolidated.py`**:
   - `start_simple_server()` - Test server
   - `add_sample_citation()` - Sample data
   - `verify_casehold_citations()` - Verification tests

### External Dependencies
1. **CourtListener API** - Primary citation verification
2. **Redis** - Task queuing and caching
3. **SQLite** - Local database storage
4. **Web Search Engines** - Fallback verification

## Performance Optimizations

1. **Caching Strategy**: Redis caching for extracted text and results
2. **Distributed Processing**: Large files split across workers
3. **Batch Processing**: Citations verified in batches
4. **Fallback Chains**: Multiple verification sources
5. **Async Processing**: Non-blocking operations with RQ workers

## Security Measures

1. **Input Validation**: All inputs sanitized and validated
2. **File Upload Security**: Secure upload directory with permissions
3. **CORS Configuration**: Restricted origins
4. **Rate Limiting**: Request throttling (if enabled)
5. **Error Handling**: Secure error responses without sensitive data

This flowchart represents the current backend architecture after consolidation, showing how the system efficiently processes legal documents while maintaining security and performance. 