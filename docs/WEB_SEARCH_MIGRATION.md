# Web Search Module Migration Guide

## Overview

The web search functionality has been enhanced and consolidated into a single, comprehensive module. This guide helps you migrate from the old modules to the new `ComprehensiveWebSearchEngine`.

## What's Changed

### Old Modules (Deprecated)
- `src/enhanced_web_searcher.py` - `EnhancedWebSearcher` and `EnhancedWebExtractor`
- `src/websearch_utils.py` - `LegalWebSearchEngine`
- `src/legal_database_scraper.py` - `LegalDatabaseScraper`
- `scripts/enhanced_case_name_extractor.py` - `EnhancedCaseNameExtractor`

### New Module
- `src/comprehensive_websearch_engine.py` - `ComprehensiveWebSearchEngine` and `ComprehensiveWebExtractor`

## Migration Steps

### 1. Update Imports

**Old:**
```python
from src.enhanced_web_searcher import EnhancedWebSearcher
from src.websearch_utils import LegalWebSearchEngine
from src.legal_database_scraper import LegalDatabaseScraper
```

**New:**
```python
from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine, ComprehensiveWebExtractor
```

### 2. Update Class Usage

**Old:**
```python
async with EnhancedWebSearcher() as searcher:
    result = await searcher.search_justia(citation)
```

**New:**
```python
engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
result = engine.search_cluster_canonical(cluster)
```

### 3. Enhanced Features

The new module provides:
- **All Previous Sources**: Justia, FindLaw, CourtListener, Leagle, OpenJurist, vLex, CaseMine, Casetext, Google Scholar, Bing, DuckDuckGo
- **Enhanced Washington Citations**: Advanced variants (Wn.2d → Wash.2d, Washington 2d, etc.)
- **Advanced Extraction**: Structured data, metadata, semantic HTML analysis, specialized database extraction
- **Similarity Scoring**: Intelligent case name comparison and validation
- **Better Error Handling**: Comprehensive logging and fallback strategies
- **Improved Performance**: Optimized concurrent search with intelligent prioritization

### 4. Supported Sources

| Source | Old Module | New Module | Status |
|--------|------------|------------|---------|
| Justia | ✅ | ✅ | Enhanced |
| FindLaw | ✅ | ✅ | Enhanced |
| CourtListener | ✅ | ✅ | Enhanced |
| Leagle | ✅ | ✅ | Enhanced |
| OpenJurist | ✅ | ✅ | Enhanced |
| vLex | ✅ | ✅ | Enhanced |
| CaseMine | ✅ | ✅ | Enhanced |
| Casetext | ✅ | ✅ | Enhanced |
| Google Scholar | ✅ | ✅ | Enhanced |
| Bing | ✅ | ✅ | Enhanced |
| DuckDuckGo | ✅ | ✅ | Enhanced |

### 5. Key Enhancements

#### Washington Citation Variants
```python
# Old: Basic citation handling
citation = "200 Wn.2d 72"

# New: Enhanced Washington variants
variants = extractor.generate_washington_variants(citation)
# Returns: ['200 Wash. 2d 72', '200 Washington 2d 72', '200 Wn. 2d 72', '200 Wn 2d 72', '200 Wash.2d 72']
```

#### Similarity Scoring
```python
# New: Intelligent case name comparison
similarity = extractor.calculate_similarity("Convoyant, LLC v. DeepThink, LLC", "Convoyant v. DeepThink")
# Returns: 0.840
```

#### Enhanced Case Name Extraction
```python
# New: Context-based extraction with validation
extracted_cases = extractor.extract_enhanced_case_names(text)
# Returns detailed extraction results with confidence scores
```

#### Specialized Database Extraction
```python
# New: Database-specific extraction patterns
result = extractor.extract_from_legal_database(url, html_content)
# Automatically detects and uses specialized patterns for CaseMine, vLex, Casetext, etc.
```

### 6. API Changes

#### Search Methods
All search methods now return enhanced results with:
- `case_name`: Extracted case name
- `date`: Publication/decision date
- `court`: Court information
- `url`: Canonical URL
- `source`: Source name with "(Enhanced)" suffix
- `confidence`: Confidence score (0.0-1.0)
- `verified`: Boolean verification status
- `extraction_methods`: List of extraction methods used
- `similarity_score`: Similarity to canonical name (if available)

#### Strategic Query Generation
**New:**
```python
queries = engine.generate_strategic_queries(cluster)
# Returns prioritized queries with enhanced Washington variants
```

### 7. Backward Compatibility

The old modules will continue to work but will show deprecation warnings. They will be removed in a future version.

### 8. Testing

Update your test scripts to use the new module:

```python
# test_comprehensive_websearch.py
from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine, ComprehensiveWebExtractor

def test_comprehensive_search():
    engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
    extractor = ComprehensiveWebExtractor()
    
    # Test Washington citation variants
    variants = extractor.generate_washington_variants("200 Wn.2d 72")
    print(f"Washington variants: {variants}")
    
    # Test similarity scoring
    similarity = extractor.calculate_similarity("Convoyant, LLC v. DeepThink, LLC", "Convoyant v. DeepThink")
    print(f"Similarity: {similarity}")
    
    # Test strategic query generation
    test_cluster = {
        'citations': [{'citation': '200 Wn.2d 72'}],
        'canonical_name': 'Convoyant, LLC v. DeepThink, LLC'
    }
    queries = engine.generate_strategic_queries(test_cluster)
    print(f"Generated {len(queries)} strategic queries")

if __name__ == "__main__":
    test_comprehensive_search()
```

## Benefits of Migration

1. **Better Coverage**: Enhanced Washington citation variants and specialized database extraction
2. **Improved Accuracy**: Advanced case name extraction with similarity scoring
3. **Faster Results**: Optimized concurrent processing with strategic query generation
4. **Future-Proof**: Active development and maintenance
5. **Better Error Handling**: Comprehensive logging and debugging
6. **Unified Solution**: Single comprehensive engine instead of multiple modules

## Timeline

- **Phase 1** ✅ (Completed): Deprecation warnings added to all old modules
- **Phase 2** ✅ (Current): Comprehensive websearch engine implemented with all features
- **Phase 3** (Future Release): Old modules removed

## Support

For questions or issues with migration, please refer to the comprehensive websearch engine documentation or create an issue in the project repository.

## Related Documentation

- [Upload Behavior Warning](UPLOAD_BEHAVIOR_WARNING.md) - Important information about file and URL re-upload behavior
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference 