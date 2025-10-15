# Codebase Review Report

Generated: D:\dev\casestrainer

## Summary

- Total Python files analyzed: 164
- Archived files: 2
- Files with deprecated patterns: 8
- Large functions (>100 lines): 91
- Duplicate function names: 251

## Detailed Findings

### Large Functions

- **_recover_case_name_from_citation_pattern** (784 lines) in `unified_extraction_architecture.py`
- **process_citation_task_direct** (565 lines) in `progress_manager.py`
- **process_citation_task_direct** (452 lines) in `rq_worker.py`
- **_process_citations_unified** (408 lines) in `unified_input_processor.py`
- **analyze** (408 lines) in `vue_api_endpoints_updated.py`
- **create_progress_routes_DISABLED** (345 lines) in `progress_manager.py`
- **analyze_text** (341 lines) in `vue_api_endpoints.py`
- **_extract_with_context** (321 lines) in `unified_extraction_architecture.py`
- **_wait_and_merge_verification_results** (292 lines) in `enhanced_sync_processor.py`
- **start_citation_analysis_DISABLED** (273 lines) in `progress_manager.py`
- **_try_patterns_on_context** (271 lines) in `unified_extraction_architecture.py`
- **_handle_file_upload** (269 lines) in `vue_api_endpoints_updated.py`
- **_are_citations_parallel_pair** (258 lines) in `unified_clustering_master.py`
- **fetch_url_content** (256 lines) in `progress_manager.py`
- **_convert_citations_to_dicts_simplified** (235 lines) in `enhanced_sync_processor.py`
- **_extract_case_name_intelligent** (221 lines) in `unified_extraction_architecture.py`
- **_find_best_matching_cluster_sync** (215 lines) in `unified_verification_master.py`
- **_format_clusters_for_output** (214 lines) in `unified_citation_clustering.py`
- **extract_from_text** (212 lines) in `standalone_citation_parser.py`
- **_extract_case_name_from_context** (203 lines) in `unified_citation_processor_v2.py`

### Duplicate Functions

- **__init__** in 117 files
- **validate_text_input** in 3 files
- **decorated_function** in 4 files
- **decorator** in 15 files
- **main** in 11 files
- **setup_logging** in 3 files
- **get** in 5 files
- **get_memory_stats** in 3 files
- **verify_citations_enhanced** in 3 files
- **_update_clusters_with_verification** in 3 files
- **__post_init__** in 6 files
- **extract_citation_components** in 4 files
- **_get_cache_key** in 3 files
- **_update_stats** in 3 files
- **get_stats** in 4 files
- **clear_cache** in 3 files
- **get_extractor** in 3 files
- **extract_case_name_and_date** in 3 files
- **is_valid_case_name** in 3 files
- **clean_case_name_enhanced** in 3 files

### Deprecated Patterns

- `src\async_verification_worker.py`: 1 issues
- `src\canonical_case_name_service.py`: 1 issues
- `src\enhanced_sync_processor.py`: 133 issues
- `src\progress_manager.py`: 4 issues
- `src\verification_services.py`: 1 issues
- `src\vue_api_endpoints_updated.py`: 3 issues
- `src\api\services\citation_service.py`: 6 issues
- `src\services\citation_extractor.py`: 1 issues
