# Web Search Module Migration Guide

## Overview

The web search functionality has been enhanced and consolidated into a single, comprehensive module. This guide helps you migrate from the old modules to the new `EnhancedWebSearcher`.

## What's Changed

### Old Modules (Deprecated)
- `src/optimized_web_searcher.py` - `OptimizedWebSearcher`
- `src/web_search_extractor.py` - `WebSearchExtractor`

### New Module
- `src/enhanced_web_searcher.py` - `EnhancedWebSearcher` and `EnhancedWebExtractor`

## Migration Steps

### 1. Update Imports

**Old:**
```python
from src.optimized_web_searcher import OptimizedWebSearcher
from src.web_search_extractor import WebSearchExtractor
```

**New:**
```python
from src.enhanced_web_searcher import EnhancedWebSearcher, EnhancedWebExtractor
```

### 2. Update Class Usage

**Old:**
```python
async with OptimizedWebSearcher() as searcher:
    result = await searcher.search_justia(citation)
```

**New:**
```python
async with EnhancedWebSearcher() as searcher:
    result = await searcher.search_justia(citation)
```

### 3. Enhanced Features

The new module provides:
- **More Sources**: vLex, CaseMine, Casetext, Google Scholar, Bing, DuckDuckGo
- **Advanced Extraction**: Structured data, metadata, semantic HTML analysis
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
| vLex | ❌ | ✅ | New |
| CaseMine | ❌ | ✅ | New |
| Casetext | ❌ | ✅ | New |
| Google Scholar | ❌ | ✅ | New |
| Bing | ✅ | ✅ | Enhanced |
| DuckDuckGo | ✅ | ✅ | Enhanced |

### 5. API Changes

#### Search Methods
All search methods now return enhanced results with:
- `case_name`: Extracted case name
- `date`: Publication/decision date
- `court`: Court information
- `url`: Canonical URL
- `source`: Source name with "(Enhanced)" suffix
- `confidence`: Confidence score (0.0-1.0)
- `verified`: Boolean verification status

#### Concurrent Search
**Old:**
```python
result = await searcher.search_parallel(citation, max_workers=3)
```

**New:**
```python
result = await searcher.search_multiple_sources(citation, max_concurrent=10)
```

### 6. Backward Compatibility

The old modules will continue to work but will show deprecation warnings. They will be removed in a future version.

### 7. Testing

Update your test scripts to use the new module:

```python
# test_enhanced_web_search.py
import asyncio
from src.enhanced_web_searcher import EnhancedWebSearcher

async def test_enhanced_search():
    async with EnhancedWebSearcher() as searcher:
        # Test all sources
        result = await searcher.search_multiple_sources("410 U.S. 113")
        print(f"Found: {result.get('case_name')} via {result.get('source')}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_search())
```

## Benefits of Migration

1. **Better Coverage**: Access to more legal databases
2. **Improved Accuracy**: Advanced extraction techniques
3. **Faster Results**: Optimized concurrent processing
4. **Future-Proof**: Active development and maintenance
5. **Better Error Handling**: Comprehensive logging and debugging

## Timeline

- **Phase 1** ✅ (Completed): Deprecation warnings added
- **Phase 2** ✅ (Current): Old modules marked as deprecated with prominent warnings
- **Phase 3** (Future Release): Old modules removed

## Support

For questions or issues with migration, please refer to the enhanced web searcher documentation or create an issue in the project repository.

## Related Documentation

- [Upload Behavior Warning](UPLOAD_BEHAVIOR_WARNING.md) - Important information about file and URL re-upload behavior
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference 