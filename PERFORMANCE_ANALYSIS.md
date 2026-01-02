# CaseStrainer Performance Analysis & Optimization Plan

## Processing Pipeline Flow

### Current Architecture
```
Input (URL/File/Text)
  ↓
[1] Document Extraction (PDF/URL → Text)
  ↓
[2] Citation Extraction (Regex + Eyecite)
  ↓
[3] Case Name/Date Extraction (per citation, with full text context)
  ↓
[4] Verification (CourtListener API - batch processing)
  ↓
[5] Parallel Citation Propagation
  ↓
[6] Clustering (with extracted names/years)
  ↓
[7] Response Formatting
```

## Identified Bottlenecks

### 1. **Case Name Extraction (HIGH PRIORITY)**
**Location**: `src/unified_citation_processor_v2.py:3868-4000`
**Issue**: 
- Extracts case names 3 times per citation (master, context, regex)
- Each extraction scans full document text (up to 500 chars backward)
- For 100 citations = 300 extraction attempts × 500 chars = 150KB of text scanning
**Impact**: ~5-10 seconds for 100 citations
**Optimization**: 
- Cache extraction results per citation position
- Extract once, reuse results
- Use smaller context windows when possible

### 2. **Verification API Calls (MEDIUM PRIORITY)**
**Location**: `src/unified_verification_master.py:verify_citations_batch`
**Issue**:
- Batch size is 60, but progress callback called after each batch
- No connection pooling optimization
- Retry logic may cause delays
**Impact**: ~2-5 seconds per batch (network dependent)
**Optimization**:
- Increase batch size if API allows
- Optimize retry backoff
- Use connection pooling

### 3. **Duplicate Extraction Paths (HIGH PRIORITY)**
**Issue**:
- `clean_extraction_pipeline.py` calls verification internally
- `unified_processing_pipeline.py` also calls verification
- Results in double verification for some paths
**Impact**: 2x verification time
**Optimization**: Remove verification from clean_extraction_pipeline (already done in unified pipeline)

### 4. **Excessive Logging (LOW PRIORITY)**
**Issue**:
- Hundreds of `logger.warning()` calls per document
- String formatting overhead
- File I/O overhead
**Impact**: ~1-2 seconds for large documents
**Optimization**: 
- Use `logger.debug()` for verbose logs
- Conditional logging based on config
- Batch log messages

### 5. **Clustering Redundancy (MEDIUM PRIORITY)**
**Location**: `src/unified_clustering_master.py`
**Issue**:
- Re-extracts case names during clustering
- Duplicate proximity calculations
**Impact**: ~1-2 seconds
**Optimization**: Use pre-extracted names from citations

## Optimization Plan

### Phase 1: Quick Wins (No Quality Loss)
1. ✅ Remove verification from `clean_extraction_pipeline.py` (already handled by unified pipeline)
2. ✅ Cache case name extraction results
3. ✅ Reduce logging verbosity (use debug level)
4. ✅ Optimize context window sizes

### Phase 2: Architecture Improvements
1. Consolidate duplicate extraction functions
2. Remove stubs and disabled code
3. Optimize batch verification
4. Improve clustering efficiency

### Phase 3: Advanced Optimizations
1. Parallel case name extraction
2. Smart caching of verification results
3. Incremental clustering

## Expected Performance Improvements

| Phase | Optimization | Expected Time Savings | Quality Impact |
|-------|-------------|----------------------|----------------|
| 1 | Remove duplicate verification | 30-50% | None (same results) |
| 1 | Cache case name extraction | 20-30% | None (same results) |
| 1 | Reduce logging | 5-10% | None (debug logs still available) |
| 2 | Consolidate functions | 10-15% | Improved (less confusion) |
| 2 | Remove stubs | 2-5% | Improved (cleaner code) |
| 3 | Parallel extraction | 30-40% | None (same results) |

**Total Expected Improvement**: 50-70% faster processing for large documents

