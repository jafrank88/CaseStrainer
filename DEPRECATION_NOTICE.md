# CaseStrainer Deprecation Notice

## ⚠️ **DEPRECATED METHODS**

The following methods have been deprecated and will be removed in a future version of CaseStrainer. Please update your code to use the recommended alternatives.

## ❌ **Deprecated Methods**

### 1. `_verify_with_courtlistener(citation)`
- **Status**: DEPRECATED
- **Reason**: Internal method, replaced by unified workflow
- **Replacement**: `verify_citation_unified_workflow(citation)`

### 2. `_verify_with_web_search(citations)`
- **Status**: DEPRECATED
- **Reason**: Slow and unreliable, replaced by CourtListener API
- **Replacement**: `verify_citation_unified_workflow(citation)`

### 3. `verify_citation(citation)` (Legacy)
- **Status**: DEPRECATED (but delegates to unified workflow)
- **Reason**: Legacy method, replaced by unified workflow
- **Replacement**: `verify_citation_unified_workflow(citation)`

## ✅ **Recommended Methods**

### **Use This (Recommended)**
```python
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()

# For single citation verification
result = verifier.verify_citation_unified_workflow(
    citation="347 U.S. 483",
    extracted_case_name="Brown v. Board of Education",  # Optional
    full_text="Some context text..."  # Optional, for case name extraction
)
```

## 📋 **Migration Guide**

### **Before (Deprecated)**
```python
# OLD WAY - Don't use these anymore
result = verifier._verify_with_courtlistener(citation)
result = verifier._verify_with_web_search([citation])
result = verifier.verify_citation(citation)  # Legacy method
```

### **After (Recommended)**
```python
# NEW WAY - Use this
result = verifier.verify_citation_unified_workflow(citation)
```

## 🔧 **Benefits of the Unified Workflow**

### **Performance**
- **Fast**: 15-second timeout instead of indefinite web searches
- **Reliable**: Uses CourtListener API directly
- **Efficient**: No fallback to slow DuckDuckGo/Google searches

### **Data Quality**
- **Rich Metadata**: Returns canonical names, URLs, dates, courts
- **Consistent**: Same format and fields returned everywhere
- **Accurate**: API-first approach with proper error handling

### **User Experience**
- **Fast Response**: Under 1 second for valid citations
- **No Hanging**: Proper timeout handling
- **Clear Results**: Both extracted and canonical case names

## 📁 **Files That Need Updates**

### **Test Files (Update These)**
- `test_web_search_remaining.py`
- `test_web_search_extraction.py`
- `test_site_specific_parsers.py`
- `test_improved_web_search.py`
- `test_early_stopping_optimization.py`

### **Example Updates**
```python
# OLD (in test files)
web_results = verifier._verify_with_web_search([citation])

# NEW
result = verifier.verify_citation_unified_workflow(citation)
```

## 🚨 **Deprecation Warnings**

When you use deprecated methods, you'll see warnings like:
```
DeprecationWarning: _verify_with_courtlistener() is deprecated. Use verify_citation_unified_workflow() instead.
DeprecationWarning: _verify_with_web_search() is deprecated. Use verify_citation_unified_workflow() instead. Web search is slow and unreliable compared to CourtListener API.
```

## 📊 **Timeline**

- **Current**: Deprecated methods show warnings but still work
- **Next Version**: Deprecated methods will be removed
- **Future**: Only unified workflow will be available

## 🛠️ **Quick Fix**

To suppress deprecation warnings temporarily:
```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# But better to update your code to use the new methods
```

## 📞 **Support**

If you need help migrating your code:
1. Check the `DEVELOPER_GUIDE.md` for examples
2. Use the test scripts to verify functionality
3. The deprecated methods still work but delegate to the unified workflow

## 🎯 **Summary**

**Use**: `verify_citation_unified_workflow(citation)`
**Don't Use**: `_verify_with_courtlistener()`, `_verify_with_web_search()`, or legacy `verify_citation()`

The unified workflow provides better performance, reliability, and data quality while maintaining backward compatibility through deprecation warnings. 