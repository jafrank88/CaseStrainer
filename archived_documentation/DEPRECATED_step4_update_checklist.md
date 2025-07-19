# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Temporary file - test results or debug output
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Step 4: Update Existing Workflows - Complete Checklist

## 🎯 **Current Status: 60% Complete**

### ✅ **Files Already Updated:**
- `src/app_final_vue.py` - ✅ Using new API
- `src/case_name_extraction_core.py` - ✅ New streamlined API
- `src/legal_case_extractor_integrated.py` - ✅ Using new core

### 🔄 **Files That Need Updates:**

## **1. src/unified_citation_processor_v2.py (CRITICAL)**

**Current Issues:**
- Line 45: `from src.case_name_extraction_core import extract_case_name_and_date_comprehensive` ❌
- Line 47: `from case_name_extraction_core import extract_case_name_and_date_comprehensive` ❌
- Line 1218: `extract_case_name_and_date_comprehensive` function call ❌

**Required Changes:**
```python
# CHANGE THESE LINES:
from src.case_name_extraction_core import extract_case_name_and_date_comprehensive
from case_name_extraction_core import extract_case_name_and_date_comprehensive

# TO:
from src.case_name_extraction_core import extract_case_name_and_date
from case_name_extraction_core import extract_case_name_and_date

# AND UPDATE FUNCTION CALLS:
# OLD: extract_case_name_and_date_comprehensive(text, citation)
# NEW: extract_case_name_and_date(text, citation)
```

## **2. src/document_processing.py (HIGH PRIORITY)**

**Current Issues:**
- Line 40: `from src.case_name_extraction_core import extract_case_name_triple_comprehensive` ❌
- Line 757: `extract_case_name_triple_comprehensive(text, citation_text)` ❌

**Required Changes:**
```python
# CHANGE:
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

# TO:
from src.case_name_extraction_core import extract_case_name_and_date

# AND UPDATE FUNCTION CALL:
# OLD: extract_case_name_triple_comprehensive(text, citation_text)
# NEW: extract_case_name_and_date(text, citation_text)
```

## **3. src/citation_extractor.py (MEDIUM PRIORITY)**

**Current Issues:**
- Line 221: `extract_case_name_triple_from_text` function call ❌
- Line 265: `extract_case_name_triple_from_text` function call ❌

**Required Changes:**
```python
# UPDATE FUNCTION CALLS:
# OLD: extract_case_name_triple_from_text(text, citation_str)
# NEW: extract_case_name_and_date(text, citation_str)
```

## **4. src/extract_case_name.py (LEGACY - LOW PRIORITY)**

**Current Issues:**
- Multiple old function calls throughout the file
- This is a legacy file that may not be actively used

**Required Changes:**
```python
# UPDATE ALL FUNCTION CALLS:
# OLD: extract_case_name_triple_comprehensive(content, citation)
# NEW: extract_case_name_and_date(content, citation)
```

## **5. src/legal_case_extractor_enhanced.py (LOW PRIORITY)**

**Current Issues:**
- Commented out imports (already handled)

**Status:** ✅ Already updated

## 🚀 **Quick Update Commands:**

### **Option 1: Manual Updates (Recommended)**
```bash
# 1. Update unified_citation_processor_v2.py
# Edit the file and change the imports and function calls

# 2. Update document_processing.py  
# Edit the file and change the imports and function calls

# 3. Update citation_extractor.py
# Edit the file and change the function calls
```

### **Option 2: Use the Update Script**
```bash
# Run the comprehensive update script
python update_extraction_functions.py
```

## 📊 **Result Handling Updates:**

### **Old API (Triple Return):**
```python
case_name, date, confidence = extract_case_name_triple_comprehensive(text, citation)
```

### **New API (Dict Return):**
```python
result = extract_case_name_and_date(text, citation)
case_name = result['case_name']
year = result['year'] 
confidence = result['confidence']
method = result['method']
```

## ✅ **Step 4 Success Criteria:**

- [x] **Found all files** that use old extraction functions ✅
- [ ] **Updated import statements** in all relevant files 🔄
- [ ] **Replaced function calls** with new API 🔄
- [ ] **All files compile** without syntax errors 🔄
- [ ] **Functionality works** as expected 🔄
- [ ] **Improved quality** - better extraction results with confidence scores 🔄

## 🎯 **Priority Order:**

1. **HIGHEST:** `src/unified_citation_processor_v2.py` - Core citation processor
2. **HIGH:** `src/document_processing.py` - Document processing pipeline  
3. **MEDIUM:** `src/citation_extractor.py` - Citation extraction service
4. **LOW:** `src/extract_case_name.py` - Legacy module

## 🔧 **Testing After Updates:**

```bash
# Test the main application
python src/app_final_vue.py

# Test the integration
python src/integration_test_streamlined.py quick

# Test individual modules
python -c "from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2; print('✅ UCP v2 works')"
```

## 📈 **Expected Benefits After Step 4:**

- ✅ **Consistent API** across all modules
- ✅ **Better error handling** with confidence scores
- ✅ **Improved extraction quality** with streamlined logic
- ✅ **Easier maintenance** with unified codebase
- ✅ **Better debugging** with detailed result structure

## 🚨 **Rollback Plan:**

If issues occur, restore from backup:
```bash
# Copy backup files back
cp backup_before_update/* src/
```

---

**Next Steps After Step 4:**
- Step 5: Production Deployment
- Step 6: Monitoring & Optimization 