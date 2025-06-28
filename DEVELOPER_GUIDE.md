# CaseStrainer Developer Guide

## Quick Reference: Verification Methods

### ✅ **Use This (Recommended)**

```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()

# For single citation verification
result = verifier.verify_citation_unified_workflow(
    citation="347 U.S. 483",
    extracted_case_name="Brown v. Board of Education",  # Optional
    full_text="Some context text..."  # Optional, for case name extraction
)

# Result includes:
# - verified: True/False
# - canonical_name: "Brown v. Board of Education"
# - extracted_case_name: From context if provided
# - url: "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
# - canonical_date: "1954-05-17"
# - court: "Supreme Court of the United States"
```

### ❌ **Don't Use These (Deprecated)**

```python
# OLD - Don't use these methods anymore
verifier._verify_with_courtlistener(citation)  # Internal method
verifier._verify_with_web_search(citations)    # Slow and unreliable
verifier.verify_citation(citation)             # Legacy method (delegates to unified)
```

## API Endpoints

### **Single Citation Verification**
```python
# POST /api/analyze
{
    "text": "347 U.S. 483"
}

# Response
{
    "verified": true,
    "canonical_name": "Brown v. Board of Education",
    "extracted_case_name": null,
    "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/",
    "canonical_date": "1954-05-17",
    "court": "Supreme Court of the United States"
}
```

### **Document Processing**
```python
# POST /api/analyze (with file or URL)
{
    "file": <file_upload> or "url": "https://example.com/document.pdf"
}

# Response includes array of verified citations
{
    "citations": [
        {
            "citation": "347 U.S. 483",
            "verified": true,
            "canonical_name": "Brown v. Board of Education",
            "extracted_case_name": "Brown v. Board",
            "url": "...",
            "canonical_date": "1954-05-17"
        }
    ]
}
```

## Key Features

### **1. Fast Verification**
- **Timeout**: 15 seconds maximum
- **API-First**: Uses CourtListener API directly
- **Fail Fast**: No fallback to slow web searches

### **2. Rich Metadata**
- **Canonical Name**: Official case name from CourtListener
- **Extracted Name**: Case name extracted from context
- **URL**: Direct link to case opinion
- **Date**: Filing date
- **Court**: Court that decided the case
- **Parallel Citations**: Alternative citation formats

### **3. Error Handling**
- **Graceful Degradation**: Returns partial results when possible
- **Clear Error Messages**: Descriptive error information
- **Timeout Protection**: Prevents hanging on slow requests

## Integration Examples

### **Flask Application**
```python
from src.vue_api_endpoints import vue_api

app = Flask(__name__)
app.register_blueprint(vue_api, url_prefix='/api')

# The /api/analyze endpoint automatically uses the unified workflow
```

### **Direct Usage**
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()

# Verify a citation
result = verifier.verify_citation_unified_workflow("410 U.S. 113")
if result.get('verified'):
    print(f"Case: {result['canonical_name']}")
    print(f"URL: {result['url']}")
    print(f"Date: {result['canonical_date']}")
```

### **Batch Processing**
```python
from src.document_processing import extract_and_verify_citations

# Process a document
citations = extract_and_verify_citations(
    text="Some legal text with citations like 347 U.S. 483",
    use_unified_workflow=True  # Uses the new unified workflow
)

for citation in citations:
    if citation.get('verified'):
        print(f"✅ {citation['citation']}: {citation['canonical_name']}")
    else:
        print(f"❌ {citation['citation']}: Not verified")
```

## Configuration

### **API Keys**
```python
# config.json
{
    "courtlistener_api_key": "your_api_key_here"
}
```

### **Database**
```python
# Automatic database initialization
# Uses SQLite at data/citations.db
# Redis for caching (optional)
```

## Testing

### **Unit Tests**
```python
# test_unified_workflow.py
def test_citation_verification():
    verifier = EnhancedMultiSourceVerifier()
    result = verifier.verify_citation_unified_workflow("347 U.S. 483")
    
    assert result['verified'] == True
    assert result['canonical_name'] == "Brown v. Board of Education"
    assert result['url'] is not None
```

### **Integration Tests**
```python
# Test the API endpoint
response = requests.post(
    "http://localhost:5000/api/analyze",
    json={"text": "347 U.S. 483"}
)
assert response.status_code == 200
assert response.json()['verified'] == True
```

## Troubleshooting

### **Common Issues**

1. **Import Errors**
   ```python
   # Make sure you're in the right directory
   import sys
   sys.path.insert(0, 'src')
   from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
   ```

2. **API Key Issues**
   ```python
   # Check config.json exists and has valid API key
   # CourtListener API key is required for verification
   ```

3. **Timeout Issues**
   ```python
   # The unified workflow has a 15-second timeout
   # If you need longer timeouts, modify the max_verification_time parameter
   ```

### **Logging**
```python
import logging
logging.basicConfig(level=logging.INFO)

# Check logs for detailed information about verification process
```

## Migration Guide

### **From Old Methods**
```python
# OLD WAY
result = verifier._verify_with_courtlistener(citation)

# NEW WAY
result = verifier.verify_citation_unified_workflow(citation)
```

### **From Web Search**
```python
# OLD WAY (slow and unreliable)
result = verifier._verify_with_web_search([citation])

# NEW WAY (fast and reliable)
result = verifier.verify_citation_unified_workflow(citation)
```

## Performance Tips

1. **Use Caching**: Results are automatically cached
2. **Batch Processing**: Use `extract_and_verify_citations()` for multiple citations
3. **Error Handling**: Always check `result.get('verified')` before using data
4. **Timeout Management**: The 15-second timeout prevents hanging

## Support

For issues or questions:
1. Check the logs for detailed error information
2. Verify API keys are configured correctly
3. Test with known valid citations first
4. Use the test scripts to verify functionality 