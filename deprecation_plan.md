# Citation Extraction Function Deprecation Plan

## Overview
This document outlines the plan to deprecate inferior citation extraction functions that use fixed context windows instead of sophisticated isolation logic, and replace them with improved versions.

## Functions to Deprecate

### 1. Inferior Context Extraction Functions

#### **Production Files (High Priority)**
- `src/unified_citation_processor_v2.py:1608` - `context_start = max(0, citation.start_index - 100)`
- `src/unified_citation_processor.py:194` - `context_start = max(0, citation_start - 100)`
- `src/unified_citation_processor.py:488` - `context_start = max(0, match.start() - 300)`
- `src/unified_citation_processor.py:1006` - `context_start = max(0, start - 200)`
- `src/standalone_citation_parser.py:95` - `context_start = max(0, citation_index - 500)`
- `src/standalone_citation_parser.py:655` - `context_start = max(0, citation_index - 200)`
- `src/standalone_citation_parser.py:882` - `context_start = max(0, citation_start - 100)`
- `src/safe_citation_processor.py:256` - `context_start = max(0, start - 100)`
- `src/enhanced_unified_citation_processor.py:598` - `context_start = max(0, start - 150)`
- `src/enhanced_extraction_utils.py:129` - `context_start = max(0, citation_index - 200)`
- `src/enhanced_extraction_utils.py:329` - `context_start = max(0, citation_index - 200)`
- `src/enhanced_extraction_utils.py:1199` - `context_start = max(0, start - 200)`
- `src/citation_services.py:543` - `context_start = max(0, span.start - 100)`

#### **Script Files (Medium Priority)**
- `scripts/adaptive_learning_pipeline.py:296` - `context_start = max(0, start - 100)`
- `scripts/enhanced_adaptive_processor.py:304` - `context_start = max(0, start - 100)`
- `scripts/enhance_case_extraction.py:153` - `context_start = max(0, pos - 200)`
- `scripts/california_citation_handler.py:167` - `context_start = max(0, match.start() - 200)`

#### **Test/Debug Files (Low Priority)**
- Various test files with fixed context windows (can be updated later)

### 2. Inferior Date Extraction Functions

#### **Production Files (High Priority)**
- `src/unified_citation_processor.py:437` - `DateExtractor.extract_date_from_context(text, start, end)`
- `src/unified_citation_processor.py:1011` - `DateExtractor.extract_date_from_context(text, start, end)`
- `src/standalone_citation_parser.py:855` - `extract_date_from_context_precise()`
- `src/standalone_citation_parser.py:894` - `extract_date_from_context()`

## Recommended Actions

### Phase 1: Create Improved Versions (High Priority)

#### 1.1 Create `_get_isolated_context_for_citation` Helper
```python
def _get_isolated_context_for_citation(self, text: str, citation_start: int, citation_end: int, all_citations: List[CitationResult] = None) -> tuple[int, int]:
    """Get isolated context boundaries for a citation using start/end positions."""
    # Create a temporary CitationResult for compatibility
    temp_citation = CitationResult(
        citation=text[citation_start:citation_end],
        start_index=citation_start,
        end_index=citation_end
    )
    return self._get_isolated_context(text, temp_citation, all_citations)
```

#### 1.2 Create `extract_date_from_context_isolated` Helper
```python
def extract_date_from_context_isolated(self, text: str, citation_start: int, citation_end: int) -> Optional[str]:
    """Extract date using isolated context to prevent cross-contamination."""
    # Use isolated context extraction
    context_start, context_end = self._get_isolated_context_for_citation(text, citation_start, citation_end)
    if context_start is None or context_end is None:
        # Fallback to reasonable window
        context_start = max(0, citation_start - 200)
        context_end = min(len(text), citation_end + 100)
    
    context = text[context_start:context_end]
    return self._extract_date_from_text(context)
```

### Phase 2: Update Production Files (High Priority)

#### 2.1 Update `src/unified_citation_processor_v2.py`
- Replace line 1608 with isolated context logic
- Update all `_extract_context` calls to use isolation

#### 2.2 Update `src/unified_citation_processor.py`
- Replace fixed context windows with isolated context
- Update date extraction calls to use isolated versions

#### 2.3 Update `src/standalone_citation_parser.py`
- Replace fixed context windows with isolated context
- Update date extraction methods

#### 2.4 Update `src/enhanced_extraction_utils.py`
- Replace fixed context windows with isolated context

### Phase 3: Update Script Files (Medium Priority)

#### 3.1 Update Script Files
- Replace fixed context windows in adaptive learning pipeline
- Update enhanced adaptive processor
- Update case extraction scripts

### Phase 4: Deprecation Warnings (Low Priority)

#### 4.1 Add Deprecation Warnings
```python
import warnings

def extract_date_from_context_old(text: str, citation_start: int, citation_end: int, context_window: int = 300) -> Optional[str]:
    """DEPRECATED: Use extract_date_from_context_isolated instead."""
    warnings.warn(
        "extract_date_from_context_old is deprecated. Use extract_date_from_context_isolated instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return extract_date_from_context_isolated(text, citation_start, citation_end)
```

## Implementation Strategy

### Step 1: Create Helper Functions
1. Create `_get_isolated_context_for_citation` helper
2. Create `extract_date_from_context_isolated` helper
3. Test helper functions thoroughly

### Step 2: Update Core Files
1. Update `unified_citation_processor_v2.py`
2. Update `unified_citation_processor.py`
3. Update `standalone_citation_parser.py`
4. Update `enhanced_extraction_utils.py`

### Step 3: Update Script Files
1. Update adaptive learning pipeline
2. Update enhanced adaptive processor
3. Update other script files

### Step 4: Add Deprecation Warnings
1. Add deprecation warnings to old functions
2. Update documentation
3. Create migration guide

## Benefits

### 1. Consistent Isolation Logic
- All context extraction will use the same sophisticated isolation logic
- Prevents cross-contamination between citations
- Improves accuracy across all extraction methods

### 2. Better Context Windows
- Increased context windows (200-300 characters instead of 100-150)
- Better coverage for long case names and complex citations
- Improved year extraction from parentheses

### 3. Maintainability
- Single source of truth for context isolation logic
- Easier to maintain and improve
- Consistent behavior across all extraction methods

### 4. Performance
- More efficient context extraction
- Reduced redundant code
- Better caching opportunities

## Risk Assessment

### Low Risk
- Helper functions are additive and don't break existing functionality
- Gradual migration allows for testing at each step
- Fallback logic ensures backward compatibility

### Medium Risk
- Some script files may need updates to function signatures
- Test files may need updates to match new behavior

### Mitigation
- Comprehensive testing at each phase
- Gradual rollout with deprecation warnings
- Maintain backward compatibility during transition

## Timeline

### Week 1: Helper Functions
- Create and test helper functions
- Update core files (unified_citation_processor_v2.py)

### Week 2: Core Files
- Update remaining core files
- Update script files

### Week 3: Testing & Documentation
- Comprehensive testing
- Add deprecation warnings
- Update documentation

### Week 4: Cleanup
- Remove deprecated functions
- Update test files
- Final validation 