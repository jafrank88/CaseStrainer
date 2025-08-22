# Citation Processor Refactoring Guide

## Overview

The `unified_citation_processor_v2.py` file has been refactored into a modular structure for better maintainability, type safety, and separation of concerns.

## New Module Structure

### 1. `citation_types.py`
**Purpose**: Type definitions and data structures
- Type aliases (`CitationList`, `CitationDict`, `VerificationResult`)
- Data classes (`CitationMatch`, `CitationContext`, `VerificationContext`)
- Constants and patterns
- Reporter mappings

### 2. `citation_utils.py`
**Purpose**: Utility functions and helpers
- Citation normalization and cleaning
- Context extraction
- Similarity calculations
- Validation functions
- Helper functions for working with citations

### 3. `citation_extractor.py`
**Purpose**: Core citation extraction logic
- `CitationExtractor` class
- Regex-based extraction
- Eyecite-based extraction
- Case name and date extraction from context
- Deduplication logic

### 4. `citation_verifier.py`
**Purpose**: Citation verification logic
- `CitationVerifier` class
- CourtListener API integration
- Landmark case verification
- Canonical service verification
- Legal web search verification

### 5. `citation_processor.py`
**Purpose**: Citation processing and clustering
- `CitationProcessor` class
- Parallel citation detection
- Citation clustering by name and year
- Confidence scoring
- State and reporter inference

### 6. `unified_citation_processor_v2_refactored.py`
**Purpose**: Main orchestrator class
- `UnifiedCitationProcessorV2` class (simplified)
- Coordinates between extractor, verifier, and processor
- Provides high-level API
- Backward compatibility functions

## Benefits of Refactoring

### 1. **Type Safety**
- Proper type annotations throughout
- No more `None` assignment issues
- Clear return types
- Better IDE support

### 2. **Maintainability**
- Single responsibility principle
- Easier to test individual components
- Clear separation of concerns
- Reduced code duplication

### 3. **Modularity**
- Components can be used independently
- Easy to swap implementations
- Better error isolation
- Simplified debugging

### 4. **Extensibility**
- Easy to add new extraction methods
- Simple to add new verification sources
- Flexible clustering algorithms
- Pluggable components

## Migration Guide

### From Old to New

#### Old Usage:
```python
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

processor = UnifiedCitationProcessorV2(config)
result = await processor.process_text(text)
```

#### New Usage:
```python
from src.unified_citation_processor_v2_refactored import UnifiedCitationProcessorV2

processor = UnifiedCitationProcessorV2(config)
result = await processor.process_text(text)
```

### Using Individual Components

#### Extraction Only:
```python
from src.citation_extractor import CitationExtractor

extractor = CitationExtractor()
citations = extractor.extract_citations(text)
```

#### Verification Only:
```python
from src.citation_verifier import CitationVerifier

verifier = CitationVerifier(api_key="your_key")
verified_citations = await verifier.verify_citations(citations)
```

#### Processing Only:
```python
from src.citation_processor import CitationProcessor

processor = CitationProcessor()
clusters = processor.cluster_citations_by_name_and_year(citations)
```

## Type Safety Improvements

### Before (Old File):
```python
def _get_extracted_case_name(self, citation: 'CitationResult') -> str:
    return citation.extracted_case_name if hasattr(citation, 'extracted_case_name') else None
```

### After (New Files):
```python
def get_extracted_case_name(citation: 'CitationResult') -> Optional[str]:
    return citation.extracted_case_name if hasattr(citation, 'extracted_case_name') else None
```

## Error Handling

The new structure provides better error handling:

1. **Component-level errors** are isolated
2. **Graceful degradation** when components fail
3. **Clear error messages** with context
4. **Proper logging** at each level

## Testing

Each module can be tested independently:

```python
# Test extraction
def test_citation_extractor():
    extractor = CitationExtractor()
    citations = extractor.extract_citations("410 U.S. 113")
    assert len(citations) == 1

# Test verification
def test_citation_verifier():
    verifier = CitationVerifier()
    result = verifier.verify_with_landmark_cases("410 U.S. 113")
    assert result["verified"] == True

# Test processing
def test_citation_processor():
    processor = CitationProcessor()
    clusters = processor.cluster_citations_by_name_and_year(citations)
    assert len(clusters) > 0
```

## Configuration

The new structure supports flexible configuration:

```python
config = ProcessingConfig(
    enable_verification=True,
    use_eyecite=True,
    COURTLISTENER_API_KEY="your_key"
)

processor = UnifiedCitationProcessorV2(config)
```

## Backward Compatibility

The refactored version maintains backward compatibility:

- Same main class name
- Same method signatures
- Same return types
- Standalone functions preserved

## Next Steps

1. **Update imports** in existing code
2. **Test the new modules** thoroughly
3. **Update documentation** to reflect new structure
4. **Consider deprecating** the old file after migration
5. **Add more unit tests** for individual components

## Performance Considerations

The refactored version should have similar or better performance:

- **Reduced memory usage** due to better structure
- **Faster imports** due to smaller modules
- **Better caching** opportunities
- **Parallel processing** possibilities

## Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all new modules are in the `src/` directory
2. **Type errors**: Check that `CitationResult` has all required attributes
3. **Async issues**: Ensure proper `await` usage for async methods
4. **Configuration**: Verify API keys and settings are correct

### Debug Mode:

Enable debug logging to see detailed processing:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This refactoring provides a solid foundation for future enhancements while maintaining the existing functionality and improving code quality significantly. 