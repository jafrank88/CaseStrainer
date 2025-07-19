# CaseStrainer Database Schema

This document describes the database schema used by CaseStrainer for storing citation data and verification results.

## Overview

CaseStrainer uses SQLite as its database system, with tables designed to store:

- Citation data
- Verification results
- User sessions
- Document metadata
- ML classification results

## Tables

### 1. Citations

Stores all citations found in documents.

```sql
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_text TEXT NOT NULL,
    case_name TEXT,
    document_id INTEGER,
    found BOOLEAN DEFAULT FALSE,
    confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

```text

### 2. Documents

Stores metadata about analyzed documents.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_date TIMESTAMP,
    status TEXT DEFAULT 'pending',
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

```text

### 3. Verification Results

Stores detailed verification results for each citation.

```sql
CREATE TABLE verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    confidence REAL DEFAULT 0.0,
    verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSON,
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

```text

### 4. Users

Stores user information for multi-user support.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

```text

### 5. Sessions

Stores user session data.

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

```text

### 6. ML Classification Results

Stores machine learning classification results for citations.

```sql
CREATE TABLE ml_classification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_id INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    classification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 0.0,
    predicted_class TEXT NOT NULL,
    features JSON,
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

```text

## Indexes

The following indexes are created to optimize query performance:

```sql
-- Citations table indexes
CREATE INDEX idx_citations_text ON citations(citation_text);
CREATE INDEX idx_citations_document ON citations(document_id);
CREATE INDEX idx_citations_found ON citations(found);

-- Verification results indexes
CREATE INDEX idx_verification_citation ON verification_results(citation_id);
CREATE INDEX idx_verification_source ON verification_results(source);
CREATE INDEX idx_verification_date ON verification_results(verification_date);

-- Documents indexes
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);

-- Sessions indexes
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

```text

## Relationships

1. **Citations to Documents**
   - One-to-many relationship
   - A document can have multiple citations
   - Each citation belongs to one document

2. **Citations to Verification Results**
   - One-to-many relationship
   - A citation can have multiple verification results
   - Each verification result belongs to one citation

3. **Users to Documents**
   - One-to-many relationship
   - A user can have multiple documents
   - Each document belongs to one user

4. **Users to Sessions**
   - One-to-many relationship
   - A user can have multiple sessions
   - Each session belongs to one user

## Data Types

- **INTEGER**: Used for IDs and counts
- **TEXT**: Used for citation text, case names, and other string data
- **REAL**: Used for confidence scores and other decimal values
- **BOOLEAN**: Used for binary flags
- **TIMESTAMP**: Used for dates and times
- **JSON**: Used for storing complex data structures

## Backup and Maintenance

The database is backed up daily using the following process:

1. Create a backup file with timestamp
2. Compress the backup
3. Store in a secure location
4. Clean up old backups (retain last 30 days)

To perform manual backup:

```bash
sqlite3 casestrainer.db ".backup 'backup_$(date +%Y%m%d).db'"

```text

## Performance Considerations

1. **Indexing Strategy**
   - Indexes are created on frequently queried columns
   - Composite indexes are used for common query patterns
   - Regular index maintenance is performed

2. **Query Optimization**
   - Use prepared statements for repeated queries
   - Implement connection pooling
   - Cache frequently accessed data

3. **Data Archiving**
   - Old verification results are archived after 1 year
   - Archived data is stored in separate tables
   - Archive process runs monthly

## Security

1. **Access Control**
   - Database access is restricted to application processes
   - No direct database access allowed
   - All queries are parameterized to prevent SQL injection

2. **Data Protection**
   - Sensitive data is encrypted at rest
   - Regular security audits are performed
   - Access logs are maintained

## Monitoring

The following metrics are monitored:

1. **Performance Metrics**
   - Query execution time
   - Index usage
   - Cache hit ratio
   - Connection pool utilization

2. **Health Metrics**
   - Database size
   - Table sizes
   - Index sizes
   - Number of connections

3. **Error Metrics**
   - Failed queries
   - Deadlocks
   - Connection timeouts
   - Data integrity errors
