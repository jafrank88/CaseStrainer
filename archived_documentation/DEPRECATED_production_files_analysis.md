# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Temporary file - test results or debug output
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Production Files Analysis - Which Files Are Actually Used

## 🎯 **Core Production Files (ACTIVELY USED):**

### **1. Main Application**
- **`src/app_final_vue.py`** ✅ **ACTIVE** - Main Flask application
  - Uses: `case_name_extraction_core`, `unified_citation_processor_v2`, `document_processing_unified`
  - Status: ✅ Updated to new API

### **2. Core Processing Modules**
- **`src/unified_citation_processor_v2.py`** ✅ **ACTIVE** - Core citation processor
  - Uses: `case_name_extraction_core`, `websearch_utils`, `canonical_case_name_service`
  - Status: ❌ **NEEDS FIXING** - Importing non-existent functions

- **`src/case_name_extraction_core.py`** ✅ **ACTIVE** - Streamlined extraction
  - Provides: `extract_case_name_and_date`, `extract_case_name_only`, `extract_year_only`
  - Status: ✅ New streamlined API

- **`src/document_processing_unified.py`** ✅ **ACTIVE** - Document processing
  - Uses: `unified_citation_processor_v2`
  - Status: ✅ Working correctly

### **3. Supporting Services**
- **`src/websearch_utils.py`** ✅ **ACTIVE** - Web search functionality
- **`src/canonical_case_name_service.py`** ✅ **ACTIVE** - Canonical name service
- **`src/api/services/citation_service.py`** ✅ **ACTIVE** - Citation service
- **`src/config.py`** ✅ **ACTIVE** - Configuration management

## ❌ **Files with Import Issues:**

### **`src/unified_citation_processor_v2.py` - CRITICAL FIX NEEDED**
**Current Issues:**
```python
# Lines 45, 47, 1218 - Importing non-existent function
from src.case_name_extraction_core import extract_case_name_and_date_comprehensive  # ❌

# Lines 1214, 1525 - Importing non-existent functions  
from src.case_name_extraction_core import extract_case_name_improved  # ❌
from src.case_name_extraction_core import extract_year_improved  # ❌

# Lines 54, 56 - Importing non-existent module
from src.case_name_extraction_core import date_extractor  # ❌
```

**Required Fixes:**
```python
# CHANGE TO:
from src.case_name_extraction_core import extract_case_name_and_date  # ✅
from src.case_name_extraction_core import extract_case_name_only  # ✅
from src.case_name_extraction_core import extract_year_only  # ✅
# Remove date_extractor import (not available)
```

## 🔄 **Legacy Files (DEPRECATED):**

### **`src/document_processing.py`** ⚠️ **DEPRECATED**
- Status: Marked as deprecated
- Used by: Test files only (not production)
- Action: Can be safely ignored

### **`src/extract_case_name.py`** ⚠️ **LEGACY**
- Status: Legacy module
- Used by: Test files only (not production)
- Action: Can be safely ignored

### **`src/citation_extractor.py`** ⚠️ **LEGACY**
- Status: Legacy module
- Used by: Test files only (not production)
- Action: Can be safely ignored

## 🚨 **CRITICAL ISSUE TO FIX:**

The **`src/unified_citation_processor_v2.py`** file is importing functions that don't exist in the current `case_name_extraction_core.py`. This will cause import errors when the application starts.

**Functions it's trying to import (but don't exist):**
- `extract_case_name_and_date_comprehensive` ❌
- `extract_case_name_improved` ❌
- `extract_year_improved` ❌
- `date_extractor` ❌

**Functions that actually exist:**
- `extract_case_name_and_date` ✅
- `extract_case_name_only` ✅
- `extract_year_only` ✅
- `extract_case_name_triple_comprehensive` ✅

## 🎯 **Immediate Action Required:**

**Fix `src/unified_citation_processor_v2.py` imports:**

```python
# Lines 45, 47, 1218 - Change from:
from src.case_name_extraction_core import extract_case_name_and_date_comprehensive

# To:
from src.case_name_extraction_core import extract_case_name_and_date

# Lines 1214, 1525 - Change from:
from src.case_name_extraction_core import extract_case_name_improved
from src.case_name_extraction_core import extract_year_improved

# To:
from src.case_name_extraction_core import extract_case_name_only
from src.case_name_extraction_core import extract_year_only

# Lines 54, 56 - Remove:
from src.case_name_extraction_core import date_extractor
```

## 📊 **Production File Summary:**

### **✅ ACTIVE PRODUCTION FILES:**
1. `src/app_final_vue.py` - Main Flask app ✅
2. `src/unified_citation_processor_v2.py` - Core processor ❌ (needs import fix)
3. `src/case_name_extraction_core.py` - Extraction core ✅
4. `src/document_processing_unified.py` - Document processing ✅
5. `src/websearch_utils.py` - Web search ✅
6. `src/canonical_case_name_service.py` - Canonical service ✅
7. `src/api/services/citation_service.py` - Citation service ✅
8. `src/config.py` - Configuration ✅

### **⚠️ LEGACY/DEPRECATED FILES:**
- `src/document_processing.py` - Deprecated
- `src/extract_case_name.py` - Legacy
- `src/citation_extractor.py` - Legacy

**Total Production Files: 8**
**Files Needing Fixes: 1 (unified_citation_processor_v2.py)** 