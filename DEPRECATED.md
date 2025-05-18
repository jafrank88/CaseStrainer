# Deprecated Components

This document tracks components that have been removed or are marked for removal from the CaseStrainer codebase.

## Removed Components (2024)

### Test Files
- `test_url.py` - URL testing script
- `test_url_analysis.py` - URL analysis testing
- `test_validate_citation.py` - Citation validation testing
- `test_fetch_url.py` - URL fetching testing
- `test_citation_extraction.py` - Citation extraction testing
- `test_citation_validation.py` - Citation validation testing
- `test_citation_lookup.py` - Citation lookup testing
- `test_eyecite.py` - Eyecite library testing
- `test_brief_citations.py` - Brief citations testing
- `test_citations.py` - Citation testing utilities (moved to archive)

### Development Scripts
- `create_test_pdf.py` - PDF creation for testing
- `run_multiple_instances.py` - Multiple instance runner
- `test_production_normalize.py` - Production normalization testing

### Source Files
- `src/simple_citation_verifier.py` - Simple citation verification
- `src/enhanced_citation_verifier.py` - Enhanced citation verification
- `src/multi_source_verifier.py` - Multi-source verification
- `src/fixed_multi_source_verifier.py` - Fixed multi-source verification
- `src/enhanced_multi_source_verifier.py` - Enhanced multi-source verification

### Brief Processing Scripts
- `src/process_briefs.py` - General brief processing
- `src/process_wa_briefs.py` - WA brief processing
- `src/process_existing_wa_briefs.py` - Existing WA brief processing
- `src/process_downloaded_wa_briefs.py` - Downloaded WA brief processing
- `src/process_c_drive_wa_briefs.py` - C-drive WA brief processing

### API Files
- `src/vue_api.py` - Vue API implementation
- `src/serve_vue.py` - Vue serving script

### Temporary Files
- `extracted_pdf_text.txt` - Temporary PDF text extraction

### Folders and Directories
- `deprecated_scripts/` - Moved to archive (2024-05-13)
- `old files/` - Moved to archive (2024-05-13)
- `nginx-1.27.5/` - Moved to archive (2024-05-13)
- `nginx-1.24.0/` - Renamed to `nginx/` (2024-05-13)

## Components Marked for Review

### Build and Development Tools
- `hyperscan/` - Hyperscan library source
- `python-hyperscan/` - Python Hyperscan bindings
- `vcpkg/` - C++ package manager

### Directories
- `deployment_package_v2/` - Contains production-ready application
- `casestrainer_sessions/` - Session storage

### Cache and Temporary Directories
- `__pycache__/` directories (cleanup script available at `scripts/cleanup_pycache.py`)

### Remaining Test Files
- `src/test_hyperscan.py` - Hyperscan functionality testing
- `src/comprehensive_test.py` - Comprehensive testing suite
- `src/comprehensive_validator_test.py` - Validator testing suite

## Cleanup Actions

1. **Completed**:
   - Removed unused test files
   - Removed redundant source files
   - Removed temporary files
   - Removed deprecated API files
   - Created cleanup script for `__pycache__` directories
   - Moved `test_citations.py` to archive
   - Moved `deprecated_scripts/` to archive
   - Moved `old files/` to archive
   - Consolidated nginx versions (moved 1.27.5 to archive, renamed 1.24.0 to `nginx/`)

2. **Pending**:
   - Review and potentially remove build tools
   - Clean up cache directories
   - Review remaining test files in `src/` directory

## Notes

- Some files were kept due to potential dependencies or binary nature
- Review these files manually before removal
- Consider moving to archive instead of deletion
- Update documentation if needed
- Test files in `src/` directory may be needed for core functionality
- `deployment_package_v2/` contains production-ready application and should be kept

## Future Cleanup

1. **High Priority**:
   - Consolidate remaining test files
   - Clean up configuration files
   - Remove duplicate functionality
   - Review and archive deployment packages

2. **Medium Priority**:
   - Clean up cache directories using new script
   - Update documentation
   - Review Hyperscan-related files

3. **Low Priority**:
   - Review and potentially remove build tools
   - Clean up session storage 