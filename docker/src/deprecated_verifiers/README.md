# Deprecated Verifiers

## Overview
This directory contains legacy citation verifier implementations that have been deprecated in favor of the canonical `EnhancedMultiSourceVerifier`.

## Why These Are Deprecated

### **Performance Issues**
- Legacy verifiers were slow and unreliable
- Multiple web search sources were mostly stub implementations
- No proper caching or rate limiting

### **Maintenance Burden**
- Multiple duplicate implementations
- Inconsistent APIs and return formats
- Difficult to maintain and update

### **Better Alternative Available**
- `EnhancedMultiSourceVerifier` provides all valuable features
- Fast, reliable CourtListener API integration
- Comprehensive format analysis and error reporting
- Proper caching, rate limiting, and error handling

## Key Legacy Verifiers

### **Citation Verifiers**
- `multi_source_verifier_unused.py` - Original multi-source verifier
- `enhanced_citation_verifier_unused.py` - Enhanced version with more sources
- `fixed_multi_source_verifier_unused.py` - Fixed version of multi-source verifier
- `simple_citation_verifier_unused.py` - Simple pattern-based verifier
- `landmark_cases_unused.py` - Landmark cases database (removed from system)

### **Test Files**
- `test_*.py` - Various test files for legacy verifiers
- `comprehensive_validator_test_unused.py` - Comprehensive testing suite
- `standalone_test_verifier_unused.py` - Standalone testing script

### **Processing Scripts**
- `process_*.py` - Various citation processing scripts
- `analyze_*.py` - Citation analysis scripts
- `extract_*.py` - Citation extraction scripts

## Valuable Features Moved to EnhancedMultiSourceVerifier

### ✅ **Successfully Migrated**
1. **Volume Range Validation** - Comprehensive validation for all reporter series
2. **Citation Format Analysis** - Detailed regex-based pattern matching
3. **Likelihood Scoring System** - Sophisticated scoring for real vs. fictional citations
4. **Enhanced Error Explanations** - Clear, actionable feedback
5. **Integrated Workflow** - Format analysis when verification fails

### ❌ **Intentionally Excluded**
1. **Landmark Cases Database** - No longer maintained
2. **Multiple Web Search Sources** - Stub implementations, not fully functional

## Migration Guide

### **For Developers**
```python
# OLD (deprecated)
from docker.src.multi_source_verifier_unused import MultiSourceVerifier
verifier = MultiSourceVerifier()
result = verifier.verify_citation(citation)

# NEW (canonical)
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation_unified_workflow(citation)
```

### **For API Users**
- **Endpoint**: `/casestrainer/api/analyze` (already uses unified workflow)
- **Response**: Now includes format analysis and likelihood scores
- **Error Messages**: More detailed and actionable

## Current Canonical Verifier

### **Location**
`src/enhanced_multi_source_verifier.py`

### **Key Features**
- ✅ CourtListener API integration (primary source)
- ✅ Washington citation normalization (`Wn.` → `Wash.`)
- ✅ Volume range validation
- ✅ Citation format analysis
- ✅ Likelihood scoring system
- ✅ Enhanced error explanations
- ✅ Comprehensive caching and rate limiting
- ✅ Case name extraction from context
- ✅ Date extraction from citations

### **Usage**
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation_unified_workflow(
    citation="149 Wn.2d 647",
    extracted_case_name="State v. Rohrich",
    use_cache=True,
    use_api=True
)
```

## Testing

### **Test the Canonical Verifier**
```bash
# Test with valid citation
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "410 U.S. 113 (1973)"}'

# Test with invalid citation
curl -X POST http://localhost:5000/casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "999 F.999d 999 (2025)"}'
```

## Conclusion

All legacy verifiers have been deprecated in favor of the `EnhancedMultiSourceVerifier`. The canonical verifier provides:

- **Better Performance**: Fast, reliable CourtListener API
- **Better Features**: Volume validation, format analysis, likelihood scoring
- **Better Error Reporting**: Detailed explanations and actionable feedback
- **Better Maintainability**: Single, well-tested implementation

**Do not use any files in this directory for new development.**
