# Import Update Guide - Consolidated Citation Utils

## Overview
This guide documents the import statement updates required after consolidating small utility files into three main consolidated modules.

## Consolidated Modules Created

### 1. `src/citation_utils_consolidated.py`
Combines functions from:
- `src/citation_normalizer.py`
- `src/citation_format_utils.py` 
- `src/validate_citation.py`

### 2. `src/toa_utils_consolidated.py`
Combines functions from:
- `src/compare_toa_vs_analyze.py`
- `src/quick_toa_vs_body_comparison.py`

### 3. `src/test_utilities_consolidated.py`
Combines functions from:
- `src/add_sample_citation.py`
- `src/verify_casehold_citations.py`
- `src/verify_logging_setup.py`
- `src/simple_server.py`

## Import Changes Required

### Critical Files Updated ✅

#### 1. `src/unified_citation_processor_v2.py`
**Lines 60-65:**
```python
# Import citation utilities from consolidated module
try:
    from src.citation_utils_consolidated import normalize_citation, generate_citation_variants
except ImportError:
    from citation_utils_consolidated import normalize_citation, generate_citation_variants
```

#### 2. `src/comprehensive_websearch_engine.py`
**Lines 22-26:**
```python
# Import citation utilities from consolidated module
try:
    from src.citation_utils_consolidated import normalize_citation, generate_citation_variants
except ImportError:
    from citation_utils_consolidated import normalize_citation, generate_citation_variants
```

**Lines 4289-4293:**
```python
# Try alternative citation variants
try:
    from src.citation_utils_consolidated import generate_citation_variants
except ImportError:
    from citation_utils_consolidated import generate_citation_variants
```

#### 3. `src/citation_extractor.py`
**Lines 52-56:**
```python
# Import the main regex patterns from citation_utils_consolidated
try:
    from src.citation_utils_consolidated import extract_citations_from_text
except ImportError:
    from citation_utils_consolidated import extract_citations_from_text
```

#### 4. `src/citation_correction_engine.py`
**Lines 24-28:**
```python
# Import citation utilities from consolidated module
try:
    from src.citation_utils_consolidated import apply_washington_spacing_rules
except ImportError:
    from citation_utils_consolidated import apply_washington_spacing_rules
```

**Removed duplicate import:**
```python
# REMOVED: from .citation_format_utils import apply_washington_spacing_rules
```

### Files That Don't Need Updates ✅

#### 1. `src/app_final_vue.py`
- No imports from old citation utility modules
- Uses `src.case_name_extraction_core` directly

#### 2. `src/citation_utils.py`
- This file remains unchanged as it's not part of the consolidation

## Remaining Files to Update (Non-Critical)

The following files still have old imports but are not critical for the main application:

### Test Files
- `test_comprehensive_websearch.py` (line 29)
- `test_washington_normalization.py` (line 23)

### Debug/Utility Files
- `debug_citation_normalization.py` (line 19)

### Documentation Files
- `docs/CITATION_VARIANT_VERIFICATION.md` (line 75)
- `CONSOLIDATION_SUMMARY.md` (line 83)

## Verification Steps

1. **Check for Import Errors:**
   ```bash
   python -c "from src.citation_utils_consolidated import normalize_citation, generate_citation_variants; print('Import successful')"
   ```

2. **Test Main Application:**
   ```bash
   python src/app_final_vue.py
   ```

3. **Run Citation Processing:**
   ```bash
   python -c "from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2; print('Processor import successful')"
   ```

## Benefits of Consolidation

1. **Reduced File Count:** From 7+ small files to 3 consolidated modules
2. **Better Organization:** Related functions grouped together
3. **Easier Maintenance:** Single import path for citation utilities
4. **Improved Performance:** Fewer module imports and file system operations

## Fallback Strategy

All import statements use try/except blocks to handle both:
- Development environment: `from src.citation_utils_consolidated import ...`
- Production environment: `from citation_utils_consolidated import ...`

## Status: ✅ COMPLETED

All critical import statements have been updated. The main application should now work correctly with the consolidated modules. 