# CaseStrainer Deprecation Priority List

**Generated**: October 15, 2025

## 🎯 Immediate Actions (This Week)

### 1. Reorganize Test Files
**Impact**: High | **Risk**: Low | **Effort**: 1-2 hours

```powershell
# Run the reorganization script
.\reorganize_codebase.ps1 -DryRun  # Preview first
.\reorganize_codebase.ps1           # Execute
```

**Files to Move** (~60 files):
- All `test_*.py` → `tests/unit/`
- All `validate_*.py` → `tests/validation/`
- All `analyze_*.py` → `tests/analysis/`
- All `check_*.py` → `tests/debug/`
- All `debug_*.py` → `tests/debug/`

**Benefits**:
- Clean root directory
- Easier navigation
- Clear separation of concerns

---

### 2. Delete Archived Directories
**Impact**: Medium | **Risk**: Very Low | **Effort**: 30 minutes

**Safe to Delete** (already archived in git):
```powershell
Remove-Item -Recurse -Force archived/
Remove-Item -Recurse -Force archive_deprecated/
Remove-Item -Recurse -Force backup_before_update/
Remove-Item -Recurse -Force archive_temp_files/
```

**Space Savings**: ~50MB

**Risk Mitigation**:
- All code is in git history
- Create final backup before deletion
- Document what was removed

---

### 3. Clean Up Temporary Test Files
**Impact**: Medium | **Risk**: Low | **Effort**: 1 hour

**Candidates for Deletion**:
```
check_*.py files (if not needed)
test_health.py, test_health2.py (temporary debug files)
check_job.py, check_workers.py (temporary debug files)
various one-off analysis scripts
```

**Action**: Review each, keep essential ones in `/tests/debug/`, delete rest

---

## 🔄 Short-Term Refactoring (This Month)

### 4. Consolidate Duplicate Tests
**Impact**: High | **Risk**: Medium | **Effort**: 3-4 hours

**Duplicate Test Categories**:

#### URL Testing (5+ files)
- `test_url_complete.py`
- `test_url_direct.py`
- `test_url_full.py`
- `test_url_integration.py`
- `test_url_processing.py`

**Action**: Merge into single `tests/integration/test_url_processing.py`

#### Extraction Testing (10+ files)
- `test_extraction_*.py` (various)
- `validate_extraction_*.py` (various)

**Action**: Consolidate into:
- `tests/unit/test_case_name_extraction.py`
- `tests/validation/validate_extraction_accuracy.py`

#### Clustering Tests (8+ files)
- `test_clustering_*.py` (various)
- `check_clustering_*.py` (various)

**Action**: Merge into:
- `tests/unit/test_citation_clustering.py`
- `tests/validation/validate_clustering.py`

---

### 5. Document Deprecated Processors
**Impact**: Medium | **Risk**: Low | **Effort**: 1 hour

**Files to Deprecate** (add warnings):

```python
# src/enhanced_sync_processor_refactored.py
# Already deprecated per memory - add clear warning at top

# Any other old processor versions
```

**Template for Deprecation Warning**:
```python
"""
DEPRECATED: This module is deprecated as of October 2025.

Use: unified_citation_processor_v2.py instead

This module will be removed in v3.0.0 (Q1 2026).

Reason: Consolidated into unified processor architecture for better
        maintainability and performance.
"""
import warnings
warnings.warn(
    "enhanced_sync_processor_refactored is deprecated. "
    "Use unified_citation_processor_v2 instead.",
    DeprecationWarning,
    stacklevel=2
)
```

---

### 6. Create Proper Test Structure
**Impact**: High | **Risk**: Low | **Effort**: 2-3 hours

**New Structure**:
```
tests/
├── __init__.py
├── conftest.py (pytest configuration)
├── /unit
│   ├── __init__.py
│   ├── test_citation_extraction.py
│   ├── test_case_name_extraction.py
│   ├── test_clustering.py
│   ├── test_verification.py
│   └── test_deduplication.py
├── /integration
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_async_processing.py
│   ├── test_url_processing.py
│   └── test_full_pipeline.py
├── /validation
│   ├── __init__.py
│   ├── validate_extraction_accuracy.py
│   ├── validate_clustering.py
│   └── validate_year_extraction.py
└── /fixtures
    ├── sample_documents.py
    ├── test_citations.py
    └── mock_api_responses.py
```

**Benefits**:
- Standard pytest structure
- Easy to run specific test types
- Shared fixtures
- Better CI/CD integration

---

## 🏗️ Medium-Term Refactoring (This Quarter)

### 7. Consolidate Configuration
**Impact**: High | **Risk**: Medium | **Effort**: 4-6 hours

**Current Issues**:
- Config spread across multiple files
- Multiple `.env` files
- Hard-coded values in code

**Proposed Solution**:
```python
src/
└── config/
    ├── __init__.py
    ├── base.py (common settings)
    ├── development.py
    ├── production.py
    └── testing.py
```

**Benefits**:
- Single source of truth
- Environment-specific settings
- Easier testing
- Better secrets management

---

### 8. Refactor Citation Processing Pipeline
**Impact**: High | **Risk**: High | **Effort**: 10-15 hours

**Current State**:
- Multiple citation processor versions
- Tight coupling between extraction and verification
- Complex dependencies

**Proposed Changes**:
1. Clear interfaces between components
2. Single citation processor (current v2)
3. Pluggable verification strategies
4. Better error handling
5. Comprehensive logging

**Risks**:
- Breaking changes
- Need thorough testing
- May affect production

**Mitigation**:
- Feature flags
- Gradual rollout
- Extensive testing
- Keep old code until proven

---

### 9. Improve Documentation
**Impact**: High | **Risk**: Low | **Effort**: 6-8 hours

**Create**:
```
docs/
├── architecture/
│   ├── overview.md
│   ├── citation_processing.md
│   ├── async_workers.md
│   └── api_design.md
├── development/
│   ├── setup.md
│   ├── testing.md
│   └── contributing.md
├── deployment/
│   ├── docker.md
│   ├── production.md
│   └── maintenance.md
└── api/
    ├── endpoints.md
    └── examples.md
```

---

## 📊 Impact Analysis

### By Risk Level

#### Low Risk (Safe to do now)
- ✅ Move test files
- ✅ Delete archived directories
- ✅ Clean up temp files
- ✅ Document deprecations

#### Medium Risk (Need testing)
- ⚠️ Consolidate duplicate tests
- ⚠️ Reorganize test structure
- ⚠️ Configuration refactoring

#### High Risk (Need careful planning)
- 🚨 Refactor citation pipeline
- 🚨 Remove deprecated code
- 🚨 Major architecture changes

### By Effort

#### Quick Wins (< 2 hours)
1. Reorganize test files - 1 hour
2. Delete archived dirs - 30 min
3. Document deprecations - 1 hour

#### Medium Effort (2-5 hours)
4. Consolidate tests - 4 hours
5. Create test structure - 3 hours
6. Config consolidation - 5 hours

#### Large Effort (> 5 hours)
7. Pipeline refactoring - 15 hours
8. Documentation - 8 hours
9. Architecture improvements - 20+ hours

---

## 🎯 Recommended Execution Plan

### Week 1: Organization
- Day 1: Reorganize test files
- Day 2: Delete archived directories
- Day 3: Clean up temp files
- Day 4: Test everything still works
- Day 5: Document changes

### Week 2-3: Consolidation
- Consolidate duplicate tests
- Create proper test structure
- Update CI/CD
- Add pytest configuration

### Week 4: Documentation
- Add deprecation warnings
- Create architecture docs
- Update README
- Create developer guide

### Month 2: Refactoring
- Configuration consolidation
- Pipeline improvements
- Performance optimization
- Security review

---

## ✅ Success Criteria

### Immediate (Week 1)
- ✅ Root directory has < 10 .py files
- ✅ All tests in `/tests` directory
- ✅ No archived code in main directories
- ✅ Application still works perfectly

### Short-term (Month 1)
- ✅ All tests consolidated and organized
- ✅ Deprecation warnings in place
- ✅ Documentation updated
- ✅ CI/CD pipeline updated

### Medium-term (Quarter 1)
- ✅ Clean architecture
- ✅ Centralized configuration
- ✅ Comprehensive test coverage
- ✅ Production-ready codebase

---

## 📝 Next Steps

**Immediate Action**:
```powershell
# 1. Preview the reorganization
.\reorganize_codebase.ps1 -DryRun

# 2. Review the output

# 3. Execute if looks good
.\reorganize_codebase.ps1

# 4. Test everything
./cslaunch

# 5. Commit changes
git add .
git commit -m "Reorganize codebase: move test files to /tests directory"
```

**Questions to Answer**:
1. Are there any tests we still run regularly?
2. Which analysis scripts are still valuable?
3. What's the plan for old archived code?
4. When can we delete deprecated processors?

---

## 🤝 Need Help?

Review the full analysis in:
- `CODEBASE_DEPRECATION_ANALYSIS.md` - Complete analysis
- `reorganize_codebase.ps1` - Automated reorganization tool
- This file - Prioritized action plan

**Ready to start?** Begin with Priority 1 (Reorganize Test Files) - low risk, high impact! 🚀
