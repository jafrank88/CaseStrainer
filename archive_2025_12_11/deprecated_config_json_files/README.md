# Deprecated Files - Config.json Pattern

**Date Archived:** December 11, 2025  
**Reason:** Unused legacy files using deprecated config.json pattern

## Files in This Archive

### 1. scotus_pdf_citation_extractor.py
- **Original Location:** `src/scotus_pdf_citation_extractor.py`
- **Issue:** Uses `config.json` for configuration instead of environment variables
- **Status:** Not imported by any active code
- **Last Verified:** December 11, 2025

### 2. citation_correction.py
- **Original Location:** `src/citation_correction.py`
- **Issue:** Uses `config.json` for configuration instead of environment variables
- **Status:** Not imported by any active code
- **Last Verified:** December 11, 2025

### 3. brief_citation_analyzer.py
- **Original Location:** `src/brief_citation_analyzer.py`
- **Issue:** Uses `config.json` for configuration instead of environment variables
- **Status:** Not imported by any active code
- **Last Verified:** December 11, 2025

## Why These Were Archived

These files represent an older configuration pattern using `config.json` directly, rather than the modern approach using environment variables via `src/config.py`.

**Current Standard:**
```python
from src.config import get_config_value
api_key = get_config_value("COURTLISTENER_API_KEY", "")
```

**Deprecated Pattern (in these files):**
```python
with open("config.json", "r") as f:
    config = json.load(f)
api_key = config.get("COURTLISTENER_API_KEY")
```

## Verification

These files were confirmed as unused through:
1. Grep search for imports across entire `src/` directory
2. No active code imports or references these modules
3. Not used in main processing pipeline

## If You Need These Files

If you need to restore these files:
1. Update configuration loading to use `src/config.py`
2. Test thoroughly before re-adding to `src/`
3. Consider if the functionality is still needed or has been superseded

## Related Documentation

- **Codebase Review:** `CODEBASE_REVIEW_DEPRECATED_CONTENT.md`
- **Review Summary:** `REVIEW_SUMMARY.md`
- **Config Standard:** `src/config.py`
