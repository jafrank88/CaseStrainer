# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Migration Guide: EnhancedMultiSourceVerifier → UnifiedCitationProcessor

## Overview

The `EnhancedMultiSourceVerifier` has been deprecated and its essential functions have been consolidated into the `UnifiedCitationProcessor`. This guide helps you migrate your code to use the new unified processor.

## Key Changes

### 1. Import Changes

**Old:**
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
```

**New:**
```python
from src.unified_citation_processor import UnifiedCitationProcessor
```

### 2. Initialization Changes

**Old:**
```python
verifier = EnhancedMultiSourceVerifier()
```

**New:**
```python
processor = UnifiedCitationProcessor()
```

### 3. Method Changes

#### Single Citation Verification

**Old:**
```python
result = verifier.verify_citation(citation)
```

**New:**
```python
result = processor.verify_citation_unified_workflow(citation)
```

#### Batch Citation Verification

**Old:**
```python
results = verifier.batch_verify_citations(citations)
```

**New:**
```python
results = processor.batch_verify_citations(citations)
```

## Available Methods

The `UnifiedCitationProcessor` now includes all the essential verification methods from `EnhancedMultiSourceVerifier`:

### Core Verification Methods
- `verify_citation_unified_workflow(citation)` - Main verification method
- `batch_verify_citations(citations)` - Batch verification with rate limiting

### Supporting Methods
- `_normalize_citation(citation)` - Normalize citation format
- `_extract_citation_components(citation)` - Extract citation parts
- `_check_cache(citation)` - Check cache for existing results
- `_save_to_cache(citation, result)` - Save results to cache

### Verification Sources
- `_verify_with_landmark_cases(citation)` - Check against known landmark cases
- `_verify_with_fuzzy_matching(citation)` - Pattern-based verification
- `_verify_with_database(citation)` - Local database verification (placeholder)
- `_verify_with_courtlistener(citation)` - CourtListener API verification
- `_verify_with_langsearch(citation)` - LangSearch API verification

## Configuration

The unified processor automatically loads configuration from `config.json` in the same directory:

```json
{
    "courtlistener_api_key": "your_courtlistener_api_key",
    "langsearch_api_key": "your_langsearch_api_key"
}
```

## Cache Management

The unified processor uses a local file-based cache system:
- Cache directory: `citation_cache/`
- Cache files: JSON format with normalized citation names
- Automatic cache creation and management

## Example Migration

### Before (Old Code)
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation("410 U.S. 113")
print(f"Verified: {result['verified']}")
```

### After (New Code)
```python
from src.unified_citation_processor import UnifiedCitationProcessor

processor = UnifiedCitationProcessor()
result = processor.verify_citation_unified_workflow("410 U.S. 113")
print(f"Verified: {result['verified']}")
```

## Benefits of Migration

1. **Unified Interface**: All citation processing in one place
2. **Better Performance**: Optimized workflow with early stopping
3. **Enhanced Caching**: Improved cache management
4. **Future-Proof**: Active development and maintenance
5. **Consistent API**: Standardized method signatures

## Testing

Use the provided test script to verify the migration:

```bash
python test_unified_processor_verification.py
```

This will test:
- Citation verification workflow
- Citation normalization
- Component extraction
- Cache functionality
- Batch processing

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're importing from the correct module
2. **Configuration Missing**: Check that `config.json` exists and has valid API keys
3. **Cache Issues**: Verify the `citation_cache/` directory is writable
4. **API Errors**: Ensure API keys are valid and services are accessible

### Getting Help

If you encounter issues during migration:
1. Check the test output for specific error messages
2. Verify your configuration file
3. Test with simple citations first
4. Review the unified processor source code for method signatures

## Deprecation Timeline

- **Phase 1**: `EnhancedMultiSourceVerifier` marked as deprecated (current)
- **Phase 2**: Warning messages added to deprecated methods
- **Phase 3**: Deprecated module removed from production builds

**Recommendation**: Migrate as soon as possible to ensure continued functionality. 