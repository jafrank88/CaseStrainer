# 🚨 DEPRECATION NOTICE - Citation Extraction Methods

## Effective Date: October 16, 2025

**UPDATED:** All extraction code has been consolidated into a single source of truth.

---

## ✅ What to Use Instead - CURRENT (Oct 2025)

### **🎯 PRIMARY: unified_case_extraction_master.py**

This is THE SINGLE SOURCE OF TRUTH for all case name extraction and cleaning.

```python
from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

# Extract case name and date
result = extract_case_name_and_date_unified_master(
    text=document_text,
    citation=citation_text,
    start_index=citation_start_pos,
    end_index=citation_end_pos,
    debug=True  # Enable detailed logging
)

# Access results
case_name = result.case_name
date = result.year
confidence = result.confidence
method = result.method
```

### **🔧 For Cleaning Only:**
```python
from src.unified_case_extraction_master import get_master_extractor

extractor = get_master_extractor()
cleaned_name = extractor._clean_case_name(raw_case_name)
```

### **⚠️ DEPRECATED (But Still Works):**

These files delegate to the master but should be phased out:

```python
# DEPRECATED - Delegates to unified_case_extraction_master
from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master

# Shows deprecation warning but still works
result = extract_case_name_and_date_master(text, citation)
```

## ❌ DEPRECATED FUNCTIONS (DO NOT USE)

### **case_name_extraction_core.py (47+ functions)**
- `extract_case_name_precise()` → Use unified extractor
- `extract_case_name_with_date_adjacency()` → Use unified extractor
- `extract_case_name_from_complex_citation()` → Use unified extractor
- `extract_case_name_from_context_enhanced()` → Use unified extractor
- `extract_case_name_global_search()` → Use unified extractor
- `extract_case_name_from_text()` → Use unified extractor
- `extract_case_name_hinted()` → Use unified extractor
- `_extract_case_name_precise_boundary()` → Use unified extractor
- `_extract_case_name_simple_boundary()` → Use unified extractor
- `_extract_case_name()` → Use unified extractor
- `extract_case_name_from_citation_volume()` → Use unified extractor
- `extract_case_name_and_date()` → Use unified extractor
- `extract_case_name_only()` → Use unified extractor
- `extract_case_name_triple_comprehensive()` → Use unified extractor
- `extract_case_name_triple()` → Use unified extractor
- `extract_case_name_improved()` → Use unified extractor
- **And 30+ more functions...**

### **enhanced_sync_processor.py**
- `_extract_case_name_local()` → Use unified extractor

### **enhanced_clustering.py**
- `_extract_case_name()` → Use unified extractor

### **unified_citation_processor_v2.py**
- `_extract_case_name_from_context()` → Use unified extractor
- `_extract_case_name_candidates()` → Use unified extractor
- `_clean_extracted_case_name()` → Use unified extractor

### **standalone_citation_parser.py**
- `_extract_case_name_from_context()` → Use unified extractor
- `_extract_just_case_name()` → Use unified extractor

### **citation_extractor.py**
- `_extract_case_name_from_context()` → Use unified extractor

### **unified_case_name_extractor.py**
- `extract_case_name_and_date()` → Use unified extractor V2
- `_extract_case_name_unified()` → Use unified extractor V2
- `_extract_fallback_case_name()` → Use unified extractor V2

## 🔧 Migration Guide

### **Before (Old Way)**
```python
# Multiple different functions with inconsistent results
from src.case_name_extraction_core import extract_case_name_precise
from src.enhanced_sync_processor import _extract_case_name_local
from src.unified_citation_processor_v2 import _extract_case_name_from_context

# Different results from different functions
case_name_1 = extract_case_name_precise(context, citation)
case_name_2 = _extract_case_name_local(text, citation)
case_name_3 = _extract_case_name_from_context(text, citation_obj)
```

### **After (New Way)**
```python
# One unified function with consistent results
from src.unified_case_name_extractor_v2 import get_unified_extractor

extractor = get_unified_extractor()
result = extractor.extract_case_name_and_date(text, citation)

# Consistent, high-quality results
case_name = result.case_name
confidence = result.confidence
method = result.method
```

## 🎯 Benefits of the New Unified Extractor

1. **Consistent Results**: No more case name truncation or inconsistent extraction
2. **Better Quality**: Uses the best patterns from all 47+ functions
3. **Performance**: Optimized with caching and intelligent strategy selection
4. **Maintainability**: Single codebase instead of 47+ scattered functions
5. **Debugging**: Comprehensive logging and validation
6. **Flexibility**: Configurable extraction strategies

## 🚀 Features

- **Multiple Strategies**: Volume-based, context-based, pattern-based, global search, fallback
- **Intelligent Context Windows**: 800-1000 character windows for comprehensive coverage
- **Consistent Regex Patterns**: All patterns use the corrected, non-truncating versions
- **Confidence Scoring**: Each result includes confidence and validation scores
- **Performance Optimization**: Caching and compiled regex patterns
- **Comprehensive Validation**: Multiple validation rules to ensure quality
- **Detailed Debugging**: Extensive logging for troubleshooting

## 📝 Example Usage

```python
from src.unified_case_name_extractor_v2 import get_unified_extractor, ExtractionStrategy

extractor = get_unified_extractor()

# Extract with all strategies
result = extractor.extract_case_name_and_date(text, citation, debug=True)

# Extract with specific strategies only
result = extractor.extract_case_name_and_date(
    text=text,
    citation=citation,
    strategies=[ExtractionStrategy.VOLUME_BASED, ExtractionStrategy.CONTEXT_BASED]
)

# Access comprehensive results
print(f"Case Name: {result.case_name}")
print(f"Date: {result.date}")
print(f"Year: {result.year}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Method: {result.method}")
print(f"Strategy: {result.strategy.value}")
print(f"Validation Errors: {result.validation_errors}")
print(f"Debug Info: {result.debug_info}")
```

## ⚠️ Important Notes

1. **All old functions will show deprecation warnings**
2. **Old functions will eventually be removed in future versions**
3. **Migrate to the new unified extractor as soon as possible**
4. **The new extractor provides better results and performance**
5. **Report any issues with the new extractor for immediate fixes**

## 🔍 Testing

Run the test script to verify the new extractor works:
```bash
python test_unified_extractor.py
```

This will test all the problematic cases that were causing truncation in the old system.
