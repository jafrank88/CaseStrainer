# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# CaseTrainer Backend Architecture Flowchart

## System Overview

```mermaid
graph TB
    %% Client Layer
    subgraph "Client Layer"
        A[Vue.js Frontend] --> B[Browser Extension]
        A --> C[Word Add-in]
        A --> D[API Clients]
    end

    %% Load Balancer/Proxy Layer
    subgraph "Proxy Layer"
        E[Nginx Reverse Proxy]
        F[SSL Termination]
    end

    %% Application Layer
    subgraph "Application Layer"
        G[Flask Application<br/>src/app_final_vue.py]
        H[Waitress WSGI Server<br/>2 threads, 4G RAM limit]
    end

    %% API Layer
    subgraph "API Layer"
        I[vue_api_endpoints.py<br/>Blueprint]
        J[citation_api.py<br/>Blueprint]
    end

    %% Processing Layer
    subgraph "Processing Layer"
        K[Async Task Queue<br/>RQ + Redis]
        L[Background Workers<br/>3 RQ Workers]
        M[Background Maintenance<br/>Threading]
    end

    %% Core Services
    subgraph "Core Services"
        N[CitationExtractor<br/>Extraction Engine]
        O[EnhancedMultiSourceVerifier<br/>Verification Engine]
        P[DocumentProcessor<br/>File/URL/Text Handler]
    end

    %% Data Layer
    subgraph "Data Layer"
        Q[SQLite Database<br/>citations.db]
        R[Redis Cache<br/>Task Queue + Results]
        S[File Storage<br/>uploads/, cache/]
    end

    %% External APIs
    subgraph "External APIs"
        T[CourtListener API<br/>Primary Source]
        U[Web Search APIs<br/>Fallback Sources]
        V[Legal Databases<br/>Additional Sources]
    end

    %% Flow Connections
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> G
    G --> H
    H --> I
    H --> J
    
    I --> K
    J --> K
    K --> L
    L --> M
    
    I --> N
    I --> O
    I --> P
    J --> N
    J --> O
    J --> P
    
    N --> Q
    O --> Q
    P --> Q
    
    K --> R
    L --> R
    M --> R
    
    N --> S
    P --> S
    
    O --> T
    O --> U
    O --> V
```

## Detailed Request Flow

### 1. Document Analysis Request Flow

```mermaid
sequenceDiagram
    participant Client as Vue.js Frontend
    participant Nginx as Nginx Proxy
    participant Flask as Flask App
    participant API as vue_api_endpoints
    participant Queue as RQ Queue
    participant Worker as RQ Worker
    participant Extractor as CitationExtractor
    participant Verifier as EnhancedMultiSourceVerifier
    participant DB as SQLite Database
    participant Redis as Redis Cache
    participant External as External APIs

    Client->>Nginx: POST /casestrainer/api/analyze
    Nginx->>Flask: Forward request
    Flask->>API: Route to analyze endpoint
    
    Note over API: Validate input (file/text/URL)
    
    alt Short Citation (Immediate Response)
        API->>Verifier: verify_citation_unified_workflow()
        Verifier->>External: CourtListener API
        External-->>Verifier: Verification result
        Verifier-->>API: Result
        API-->>Flask: Immediate JSON response
        Flask-->>Nginx: Response
        Nginx-->>Client: Response
    else Long Document (Async Processing)
        API->>Queue: Enqueue task
        Queue->>Redis: Store task metadata
        API-->>Flask: Task ID response
        Flask-->>Nginx: 202 Accepted
        Nginx-->>Client: Task ID
        
        Queue->>Worker: Process task
        Worker->>Extractor: extract_citations()
        Extractor-->>Worker: Citation list
        
        loop For each citation
            Worker->>Verifier: verify_citation_unified_workflow()
            Verifier->>External: Multiple API calls
            External-->>Verifier: Results
            Verifier-->>Worker: Verification result
        end
        
        Worker->>DB: Store results
        Worker->>Redis: Store task result
        Worker-->>Queue: Task complete
        
        Client->>Nginx: GET /casestrainer/api/task_status/{task_id}
        Nginx->>Flask: Forward request
        Flask->>API: Route to task_status
        API->>Redis: Get task result
        Redis-->>API: Task result
        API-->>Flask: JSON response
        Flask-->>Nginx: Response
        Nginx-->>Client: Final results
    end
```

### 2. Citation Extraction Pipeline

```mermaid
flowchart TD
    A[Input Text/File/URL] --> B{Input Type}
    
    B -->|File| C[File Processor]
    B -->|URL| D[URL Processor]
    B -->|Text| E[Text Processor]
    
    C --> F[PDF/Word/Text Extraction]
    D --> G[Web Scraping]
    E --> H[Text Validation]
    
    F --> I[CitationExtractor]
    G --> I
    H --> I
    
    I --> J{Extraction Method}
    
    J -->|Eyecite| K[Eyecite Extraction<br/>AhocorasickTokenizer]
    J -->|Regex| L[Regex Pattern Matching<br/>Multiple Patterns]
    
    K --> M[Citation Objects]
    L --> M
    
    M --> N[Post-Processing]
    N --> O[Filter U.S.C./C.F.R.]
    N --> P[Deduplicate Citations]
    N --> Q[Group Parallel Citations]
    
    O --> R[Case Name Extraction]
    P --> R
    Q --> R
    
    R --> S[Context Extraction]
    S --> T[Final Citation List]
```

### 3. Citation Verification Pipeline

```mermaid
flowchart TD
    A[Citation Input] --> B[Clean Citation String]
    B --> C[Format Validation]
    
    C --> D{Valid Format?}
    D -->|No| E[Return Error Result]
    D -->|Yes| F[Database Check]
    
    F --> G{Found in DB?}
    G -->|Yes| H[Return Cached Result]
    G -->|No| I[CourtListener API]
    
    I --> J{Found in CourtListener?}
    J -->|Yes| K[Return Verified Result]
    J -->|No| L[Web Search APIs]
    
    L --> M{Found in Web Search?}
    M -->|Yes| N[Return Web Result]
    M -->|No| O[Calculate Likelihood Score]
    
    O --> P[Return Unverified Result]
    
    H --> Q[Store in Database]
    K --> Q
    N --> Q
    P --> Q
```

## System Components

### 1. Application Server
- **Entry Point**: `src/app_final_vue.py`
- **WSGI Server**: Waitress (2 threads, 4G RAM limit)
- **Blueprints**: `vue_api_endpoints`, `citation_api`
- **Static Files**: Vue.js frontend served from `/static`

### 2. Async Processing
- **Queue System**: Redis + RQ (Python Redis Queue)
- **Workers**: 3 RQ worker processes
- **Task Types**: File processing, URL scraping, text analysis
- **Timeout**: 10 minutes for URL tasks, 5 minutes default

### 3. Core Engines

#### CitationExtractor
- **Methods**: Eyecite + Regex patterns
- **Features**: Case name extraction, context windows, deduplication
- **Output**: Structured citation objects with metadata

#### EnhancedMultiSourceVerifier
- **Primary Source**: CourtListener API
- **Fallback Sources**: Web search, legal databases
- **Features**: Rate limiting, retry logic, confidence scoring
- **Output**: Verification results with canonical data

#### DocumentProcessor
- **File Types**: PDF, Word, RTF, ODT, HTML
- **URL Support**: Web scraping with fallbacks
- **Text Processing**: Validation, cleaning, chunking

### 4. Data Storage
- **Primary DB**: SQLite (`citations.db`)
- **Cache**: Redis (task queue, results, session data)
- **File Storage**: Uploads, extracted text, logs
- **Backup**: Automated daily backups

### 5. External Integrations
- **CourtListener API**: Primary citation verification
- **Web Search**: Google, Bing for fallback verification
- **Legal Databases**: Additional verification sources

## Performance Characteristics

### Resource Limits
- **Backend**: 4G RAM, 2 CPU cores
- **Redis**: 512M RAM
- **Workers**: 3 parallel processes
- **File Upload**: 50MB max

### Rate Limiting
- **CourtListener**: 180 requests/minute
- **Web Search**: 100 requests/minute
- **Database**: Connection pooling

### Caching Strategy
- **Citation Results**: 1 hour TTL
- **Task Results**: 1 hour TTL
- **API Responses**: 5 minutes TTL

## Security Features

### Input Validation
- File type validation
- Size limits
- Content sanitization
- SQL injection prevention

### Access Control
- CORS configuration
- Rate limiting
- Request logging
- Error masking

### Data Protection
- Secure file uploads
- Temporary file cleanup
- Sensitive data masking
- Audit logging

## Monitoring & Health Checks

### Health Endpoints
- `/casestrainer/api/health` - System health
- `/casestrainer/api/version` - Version info
- `/casestrainer/api/server_stats` - Performance metrics
- `/casestrainer/api/db_stats` - Database statistics

### Background Maintenance
- Database cleanup
- Cache expiration
- Failed task cleanup
- Performance monitoring

## Deployment Architecture

### Production Environment
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx with SSL termination
- **Load Balancing**: Nginx upstream configuration
- **Health Checks**: Automated container health monitoring

### Development Environment
- **Local Development**: Flask development server
- **Hot Reloading**: File watching and auto-restart
- **Debug Mode**: Detailed error messages and logging
- **Local Redis**: Docker container for queue management 