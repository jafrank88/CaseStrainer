# CaseStrainer Deprecation Plan

## 🚨 CRITICAL: Debug API Removed from Production

**Issue Fixed**: The `src/debug_test_api.py` was being registered as a fallback in production, causing mock data to be served instead of real citation processing.

**Action Taken**: Removed the debug API fallback registration from `src/app_final_vue.py`.

## 📋 Files to Deprecate/Move

### 🔴 **IMMEDIATE DEPRECATION (Production Risk)**

#### Debug/Test APIs (Should be moved to `deprecated_scripts/`)
- `src/debug_test_api.py` - **CRITICAL**: Was causing mock data in production
- `src/simple_test_api.py` - Test API with mock responses
- `src/debug_endpoint.py` - Debug endpoint for testing
- `src/debug_api_call.py` - Debug script for API calls
- `src/debug_complex_citation.py` - Debug script for citation processing
- `src/debug_routes.py` - Debug routes for testing

#### Test/Utility Scripts (Should be moved to `deprecated_scripts/`)
- `src/test_toa_vs_analyze_endpoint.py` - Test script
- `src/standalone_test_verifier.py` - Standalone test verifier
- `src/test_utilities_consolidated.py` - Test utilities
- `src/test_production_readiness.py` - Production readiness tests
- `src/healthcheck_robust.py` - Health check utility
- `src/healthcheck_rq.py` - RQ health check

### 🟡 **DEPRECATION CANDIDATES (Review Required)**

#### Duplicate/Outdated Files
- `src/vue_api_endpoints_updated.py` - Updated version of vue_api_endpoints.py
- `src/vue_api.py` - Alternative Vue API implementation
- `src/rq_worker_windows.py` - Windows-specific RQ worker
- `src/rq_windows_patch.py` - Windows patch for RQ
- `src/unified_citation_processor_v2_refactored.py` - Refactored version
- `src/enhanced_validator_production.py` - Production validator

#### Legacy/Consolidated Files
- `src/citation_utils.py` - Legacy citation utilities (consolidated version exists)
- `src/validate_citation.py` - DEPRECATED (marked in file)
- `src/simple_server.py` - DEPRECATED (marked in file)
- `src/citation_verification.py` - Contains deprecated functions

### 🟢 **KEEP (Production Files)**

#### Core Production Files
- `src/app_final_vue.py` - Main Flask application
- `src/vue_api_endpoints.py` - Production Vue API endpoints
- `src/rq_worker.py` - Production RQ worker
- `src/unified_citation_processor_v2.py` - Main citation processor
- `src/citation_utils_consolidated.py` - Consolidated citation utilities
- `src/case_name_extraction_core.py` - Core case name extraction
- `src/courtlistener_verification.py` - CourtListener verification
- `src/citation_clustering.py` - Citation clustering logic
- `src/document_processing_unified.py` - Document processing
- `src/standalone_citation_parser.py` - Standalone citation parser

## 🛠️ **Implementation Plan**

### Phase 1: Critical Cleanup (IMMEDIATE)
1. ✅ Remove debug API fallback from production
2. Move debug/test APIs to `deprecated_scripts/`
3. Remove deprecated imports

### Phase 2: File Organization (NEXT)
1. Move test utilities to `deprecated_scripts/`
2. Review and consolidate duplicate files
3. Update imports and references

### Phase 3: Documentation (FINAL)
1. Update documentation to reflect changes
2. Remove references to deprecated files
3. Update .gitignore and .dockerignore

## 📝 **Commands to Execute**

```bash
# Create deprecated_scripts directory if it doesn't exist
mkdir -p deprecated_scripts

# Move debug/test APIs
mv src/debug_test_api.py deprecated_scripts/
mv src/simple_test_api.py deprecated_scripts/
mv src/debug_endpoint.py deprecated_scripts/
mv src/debug_api_call.py deprecated_scripts/
mv src/debug_complex_citation.py deprecated_scripts/
mv src/debug_routes.py deprecated_scripts/

# Move test utilities
mv src/test_toa_vs_analyze_endpoint.py deprecated_scripts/
mv src/standalone_test_verifier.py deprecated_scripts/
mv src/test_utilities_consolidated.py deprecated_scripts/
mv src/test_production_readiness.py deprecated_scripts/
mv src/healthcheck_robust.py deprecated_scripts/
mv src/healthcheck_rq.py deprecated_scripts/

# Move deprecated files
mv src/validate_citation.py deprecated_scripts/
mv src/simple_server.py deprecated_scripts/
```

## ⚠️ **Warnings**

1. **Never register debug APIs in production** - This was causing mock data to be served
2. **Test thoroughly** after moving files to ensure no broken imports
3. **Update documentation** to reflect the new file structure
4. **Monitor logs** for any missing import errors after cleanup

## 🎯 **Success Criteria**

- [ ] No debug APIs registered in production
- [ ] No mock data being served
- [ ] All deprecated files moved to appropriate locations
- [ ] No broken imports or references
- [ ] Production tests pass
- [ ] Documentation updated 