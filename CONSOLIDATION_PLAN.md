# Extraction Function Consolidation Plan

## Current State (Post-Fix #43)

### ✅ PRODUCTION FUNCTION (Working Correctly)
**`UnifiedCaseExtractionMaster`** (`src/unified_case_extraction_master.py`)
- **Status:** Just fixed with Fix #43 (use original text, not normalized)
- **Strategies:** 3 strategies (position-aware, context-based, pattern-based)
- **Key Features:**
  - Handles line breaks correctly
  - Uses original text with original indices
  - Backward-only search (no forward contamination)
  - Non-greedy regex quantifiers
  - Proper Unicode handling
- **Used By:** Main extraction pipeline via `extract_case_name_and_date_master()`

### ⚠️ REDUNDANT FUNCTIONS (Should Be Deprecated)

1. **`UnifiedCaseNameExtractorV2`** (`src/unified_case_name_extractor_v2.py`)
   - Claims to consolidate 47+ functions
   - Has similar strategies but NOT FIXED with #43
   - Risk: May have same text normalization bug

2. **`UnifiedExtractionArchitecture`** (`src/unified_extraction_architecture.py`)
   - Another "unified" approach
   - Comments say "ONLY extraction method" but not actually used
   - Normalizes text early (same bug as we just fixed!)

3. **`UnifiedCaseNameExtractor`** (`src/unified_case_name_extractor.py`)
   - Older version (V1)
   - Should be fully deprecated

4. **`EnhancedCaseExtractor`** (`scripts/enhance_case_extraction.py`)
   - Script-only, not in production
   - OK to keep for testing/experiments

5. **Various deprecated/backup versions**
   - Already in backup folders
   - Can be safely ignored

## Recommended Actions

### Phase 1: Document and Verify (IMMEDIATE)
- [x] Document which function is actually in production
- [ ] Add deprecation warnings to unused functions
- [ ] Verify all imports use `UnifiedCaseExtractionMaster`

### Phase 2: Consolidate Patterns (NEXT SPRINT)
- [ ] Extract all unique regex patterns from all extractors
- [ ] Benchmark each pattern on test dataset
- [ ] Keep only the best-performing patterns
- [ ] Update `UnifiedCaseExtractionMaster` with best patterns

### Phase 3: Deprecation (FUTURE)
- [ ] Add `@deprecated` decorators to old functions
- [ ] Update all imports to use master extractor
- [ ] Remove deprecated code after 1 version grace period

## Key Lesson Learned from Fix #43

**CRITICAL:** When using character indices for text slicing:
- Indices MUST match the text version (original vs normalized)
- Text normalization (removing line breaks) shifts ALL positions
- Always use original text OR recalculate indices after normalization

This bug existed in multiple extractors. Fix #43 resolved it in the production function.

## Priority: Focus on Real Issues First

Before consolidation, address the remaining production issues:
1. **Clustering:** Parallel citations being split incorrectly
2. **Verification:** API returning wrong cases
3. **Extraction quality:** Some citations still extracting "N/A"

Consolidation is technical debt cleanup - important but not blocking users.

