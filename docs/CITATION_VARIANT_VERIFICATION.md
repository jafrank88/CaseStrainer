# Citation Variant Verification

## Overview

CaseStrainer now includes an advanced citation variant verification system that automatically generates and tests multiple citation formats to improve hit rates with the CourtListener API. This feature significantly increases the likelihood of finding and verifying citations, even when they appear in different formats in the source document.

## How It Works

### Citation Variant Generation

The system automatically generates multiple plausible variants of each extracted citation using the `generate_citation_variants()` function in `src/citation_normalizer.py`:

```python
def generate_citation_variants(citation: str) -> List[str]:
    """
    Generate all plausible variants of a citation for fallback/parallel search.
    Includes Washington-specific, normalized, and expanded forms.
    """
```

### Example Variants Generated

For a Washington citation like `171 Wash. 2d 486`, the system generates:

1. `171 Wash. 2d 486` (original)
2. `171 Wn. 2d 486` (normalized)
3. `171 Wn.2d 486` (no space)
4. `171 Washington 2d 486` (full name)
5. `171 Wn 2d 486` (no periods)

For a Federal citation like `410 U.S. 113`, the system generates:

1. `410 U.S. 113` (original)
2. `410 US 113` (no periods)
3. `410 United States 113` (full name)

## Verification Process

### Step 1: Citation-Lookup API
For each variant, the system first tries the CourtListener citation-lookup endpoint:

```python
lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
resp = requests.post(lookup_url, headers=headers, data={"text": variant}, timeout=10)
```

### Step 2: Search API Fallback
If citation-lookup fails for all variants, the system tries the search endpoint:

```python
search_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={variant}&format=json"
resp = requests.get(search_url, headers=headers, timeout=10)
```

### Step 3: Web Search Fallback
If CourtListener fails entirely, the system falls back to web search using the EnhancedWebSearcher.

## Implementation Details

### Integration with UnifiedCitationProcessorV2

The citation variant verification is integrated into the `UnifiedCitationProcessorV2` class:

```python
def _verify_with_courtlistener(self, citation: str, extracted_case_name: str = None, extracted_date: str = None) -> Dict:
    """
    Enhanced verification: Try CourtListener API first, then EnhancedWebSearcher as fallback.
    Now tries multiple citation variants to improve hit rates.
    """
    from src.citation_normalizer import generate_citation_variants
    
    # Generate citation variants to try
    citation_variants = generate_citation_variants(citation)
    logger.info(f"Trying {len(citation_variants)} citation variants for '{citation}': {citation_variants}")
    
    # Try each variant with citation-lookup endpoint first
    for variant in citation_variants:
        # ... verification logic
```

### Logging and Debugging

The system provides detailed logging of the variant testing process:

```
INFO: Trying 6 citation variants for '171 Wn.2d 486': ['171 Wn 2d 486', '171 Wash. 2d 486', '171 Washington 2d 486', '171 Wn.2d 486', '171 Wn. 2d 486', '171 Wash.2d 486']
INFO: Found citation with variant: 171 Wash. 2d 486
```

## Benefits

### Improved Hit Rates
- **Before**: Single citation format tested
- **After**: Multiple citation formats tested automatically
- **Result**: Significantly higher verification success rates

### Better User Experience
- Users don't need to manually try different citation formats
- System automatically handles format variations
- More citations are verified and show canonical data

### Robust Error Handling
- Graceful fallback between different verification methods
- Detailed logging for troubleshooting
- No single point of failure

## Testing

### Manual Testing
Use the test script to verify citation variant generation:

```bash
python test_citation_variants.py
```

This will show:
- Which citation variants are generated
- Which variants get hits in CourtListener
- The canonical data returned for each hit

### Example Test Output
```
=== TESTING CITATION VARIANT GENERATION ===

Original citation: '171 Wn.2d 486'
Generated 6 variants:
  1. '171 Wn 2d 486'
  2. '171 Wash. 2d 486'
  3. '171 Washington 2d 486'
  4. '171 Wn.2d 486'
  5. '171 Wn. 2d 486'
  6. '171 Wash.2d 486'

=== TESTING COURTLISTENER API WITH VARIANTS ===
1. Testing variant: '171 Wash. 2d 486'
   ✓ FOUND via search!
      Case: Wash. Post v. McManus
      Date: 2019-01-03
      URL: /opinion/7333806/wash-post-v-mcmanus/
```

## Configuration

### Environment Variables
- `COURTLISTENER_API_KEY`: Required for CourtListener API access
- `LANGSEARCH_API_KEY`: Optional for web search fallback

### Processing Configuration
The variant testing can be configured in the `ProcessingConfig`:

```python
config = ProcessingConfig(
    enable_verification=True,  # Enable variant testing
    debug_mode=True           # Enable detailed logging
)
```

## Performance Considerations

### API Call Optimization
- Citation-lookup endpoint is tried first (faster, more precise)
- Search endpoint is used as fallback
- Web search is used only as last resort
- Results are cached to avoid repeated API calls

### Timeout Handling
- 10-second timeout for each API call
- Graceful handling of network failures
- Detailed error logging for troubleshooting

## Troubleshooting

### Common Issues

1. **No Variants Generated**
   - Check that the citation format is recognized
   - Verify the citation normalizer is working correctly

2. **All Variants Fail**
   - Check CourtListener API key is valid
   - Verify network connectivity
   - Check API rate limits

3. **Slow Performance**
   - Monitor API call frequency
   - Check caching is working
   - Consider reducing variant generation for performance

### Debug Mode
Enable debug logging to see detailed variant testing:

```python
import logging
logging.getLogger('src.unified_citation_processor_v2').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Improvements
- **Machine Learning**: ML-based variant generation
- **Custom Variants**: User-defined variant patterns
- **Performance Optimization**: Parallel API calls for variants
- **Advanced Caching**: Smarter caching strategies

### API Integration
- **Additional Sources**: Integration with more legal databases
- **Batch Processing**: Batch variant testing for multiple citations
- **Real-time Updates**: Real-time variant testing results

## Conclusion

The citation variant verification system significantly improves the accuracy and reliability of citation verification in CaseStrainer. By automatically testing multiple citation formats, the system ensures that more citations are found and verified, providing users with better results and more comprehensive canonical data. 