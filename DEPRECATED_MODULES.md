# Deprecated Modules

This document lists all deprecated modules in the CaseStrainer project and their replacements.

## Overview

All deprecated functionality has been integrated into the **unified pipeline**:
- **UnifiedCitationProcessor** (`src/unified_citation_processor.py`)
- **extract_case_name_triple** (`src/case_name_extraction_core.py`)

## Deprecated Modules

### Core Processing Modules

| Deprecated Module | Replacement | Status |
|------------------|-------------|---------|
| `src/enhanced_citation_processor.py` | `UnifiedCitationProcessor` | ✅ Deprecated |
| `src/citation_processor.py` | `UnifiedCitationProcessor` | ✅ Deprecated |
| `src/citation_extractor.py` | `UnifiedCitationProcessor` | ✅ Deprecated |
| `src/citation_verification.py` | `EnhancedMultiSourceVerifier` | ✅ Deprecated |

### Case Name Extraction Modules

| Deprecated Module | Replacement | Status |
|------------------|-------------|---------|
| `src/enhanced_case_name_extractor.py` | `extract_case_name_triple` | ✅ Deprecated |
| `src/archived_case_name_extraction.py` | `extract_case_name_triple` | ✅ Deprecated |
| `src/extract_case_name.py` (most functions) | `extract_case_name_triple` | ✅ Deprecated |

### Specialized Modules

| Deprecated Module | Replacement | Status |
|------------------|-------------|---------|
| `src/landmark_cases.py` | Removed (database deleted) | ✅ Deprecated |

### Deprecated Scripts

All scripts in `deprecated_scripts/` directory are deprecated.

## Migration Guide

### For Citation Processing

**Old:**
```python
from src.enhanced_citation_processor import EnhancedCitationProcessor
processor = EnhancedCitationProcessor()
result = processor.process_text(text)
```

**New:**
```python
from src.unified_citation_processor import UnifiedCitationProcessor
processor = UnifiedCitationProcessor()
result = processor.process_text(text)
```

### For Case Name Extraction

**Old:**
```python
from src.enhanced_case_name_extractor import EnhancedCaseNameExtractor
extractor = EnhancedCaseNameExtractor()
result = extractor.get_canonical_case_name(citation)
```

**New:**
```python
from src.case_name_extraction_core import extract_case_name_triple
result = extract_case_name_triple(text, citation)
```

### For Citation Verification

**Old:**
```python
from src.citation_verification import CitationVerifier
verifier = CitationVerifier()
result = verifier.verify_citation(citation)
```

**New:**
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation_unified_workflow(citation)
```

## Features Integrated

The unified pipeline now includes all the best features from deprecated modules:

### From Enhanced Citation Processor
- ✅ Complex citation detection and parsing
- ✅ Parallel citation handling
- ✅ Citation grouping and deduplication
- ✅ Multi-source verification

### From Enhanced Case Name Extractor
- ✅ Citation normalization and variant generation
- ✅ Washington-specific citation handling
- ✅ API result caching (optional)
- ✅ Multi-strategy extraction

### From Extract Case Name
- ✅ Literal extraction from document text
- ✅ Context-based extraction with narrow windows
- ✅ Date adjacency extraction
- ✅ Global search fallback
- ✅ Canonical name fallback

### From Citation Verification
- ✅ CourtListener API integration
- ✅ Google Scholar fallback
- ✅ Rate limiting and retry logic
- ✅ Comprehensive error handling

## Benefits of Migration

1. **Unified Interface**: Single processor for all citation handling
2. **Better Performance**: Optimized pipeline with fewer redundant calls
3. **Improved Accuracy**: Best features from all modules combined
4. **Easier Maintenance**: Single codebase to maintain
5. **Better Logging**: Comprehensive debug logging throughout
6. **Citation Variants**: Better API lookup success with normalization

## Removal Timeline

- **Phase 1**: All modules marked as deprecated with warnings ✅
- **Phase 2**: Deprecated modules moved to `deprecated/` directory (future)
- **Phase 3**: Deprecated modules removed entirely (future)

## Testing

To test the unified pipeline:

```bash
# Enable debug logging
export LOG_LEVEL_CASE_NAME_EXTRACTION=DEBUG

# Test with PowerShell launcher
.\dplaunch2.ps1 -Mode Production -DebugCaseNameExtraction
```

## Support

If you encounter issues with the unified pipeline, check:
1. Debug logs for extraction details
2. Citation variant generation
3. API response handling
4. Error fallback mechanisms

All deprecated modules will show deprecation warnings when imported, directing users to the unified pipeline. 