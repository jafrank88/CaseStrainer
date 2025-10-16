# CaseStrainer Cleanup Progress Tracker

**Started**: October 15, 2025  
**Goal**: Finish codebase organization  
**Est. Time**: 8-12 hours

---

## 📊 Overall Progress

- [x] **Phase 1**: Test file organization (149 files)
- [x] **Phase 2**: Script organization (19 files)
- [ ] **Stage 1**: Delete old files (est. ~40 files)
- [ ] **Stage 2**: Move scripts (est. ~15 files)
- [ ] **Stage 3**: Move production code (est. ~35 files)
- [ ] **Stage 4**: Review unknowns (est. ~70 files)
- [ ] **Stage 5**: Final cleanup

**Current**: 157 files in root → Target: 4 files in root

---

## ✅ Stage 1: Quick Wins (High Priority)

### Task 1.1: Delete Deprecated Files
- [ ] verify_no_deprecated_calls.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete deprecated file"`

### Task 1.2: Delete Simple Test Files (15 files)
- [ ] simple_endpoint_test.py
- [ ] simple_name_test.py
- [ ] simple_pdf_routing_test.py
- [ ] simple_pdf_test.py
- [ ] simple_pdf_wl_test.py
- [ ] simple_test.py
- [ ] simple_url_test.py
- [ ] simple_wl_test.py
- [ ] simple_extract.py
- [ ] simple_upload.py
- [ ] simple_url_check.py
- [ ] simple_cl_verify.py
- [ ] simple_clustering_debug.py
- [ ] simple_context_check.py
- [ ] simple_server.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete simple test files"`

### Task 1.3: Delete Quick Test Files (6 files)
- [ ] quick_pdf_test.py
- [ ] quick_test.py
- [ ] quick_test_24-2626.py
- [ ] quick_test_direct.py
- [ ] quick_url_test.py
- [ ] quick_wl_test.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete quick test files"`

### Task 1.4: Delete Direct Test Files (3 files)
- [ ] direct_extraction_test.py
- [ ] direct_extraction_test_fixed.py
- [ ] direct_test.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete direct test files"`

### Task 1.5: Delete Final/Focused Test Files (8 files)
- [ ] final_clustering_fix.py
- [ ] final_contamination_test.py
- [ ] final_test_summary.py
- [ ] final_verification_test.py
- [ ] get_unverified_citations_final.py
- [ ] focused_url_test.py
- [ ] focused_wl_test.py
- [ ] minimal_wl_test.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete final/focused test files"`

### Task 1.6: Delete Old Analysis Files (6 files)
- [ ] crosscontamination_analysis.py
- [ ] date_overwrite_analysis.py
- [ ] document_vs_network_analysis.py
- [ ] critical_issues_analysis.py
- [ ] deprecation_analysis.py
- [ ] review_mismatches_report.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete old analysis files"`

**Stage 1 Totals**: ~39 files deleted  
**Est. Time**: 1-2 hours  
**Status**: [ ] Complete

---

## 📦 Stage 2: Move Scripts (Medium Priority)

### Task 2.1: Move Entry Point Scripts (11 files)
- [ ] launch_app.py → scripts/
- [ ] run.py → scripts/
- [ ] run_app.py → scripts/
- [ ] run_test_with_output.py → scripts/
- [ ] start_app.py → scripts/
- [ ] start_backend.py → scripts/
- [ ] start_flask.py → scripts/
- [ ] start_server.py → scripts/
- [ ] start_worker.py → scripts/
- [ ] build_and_run.py → scripts/
- [ ] do_cleanup.py → scripts/
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Move entry point scripts"`

### Task 2.2: Move Analysis Tools (4 files keep, 4 delete)
**Keep and move**:
- [ ] complex_citation_analyzer.py → scripts/analysis/
- [ ] pdf_structure_analysis.py → scripts/analysis/
- [ ] review_codebase_comprehensive.py → scripts/analysis/
- [ ] simple_reporter_analysis.py → scripts/analysis/

**Delete**:
- [ ] evaluate_extraction_with_toa.py
- [ ] evaluate_production_results.py
- [ ] examine_toa_context.py
- [ ] analyze_remaining_files.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Move analysis tools"`

### Task 2.3: Delete Documentation Files (2 files)
- [ ] critical_fixes_summary.py
- [ ] diagnosis_report.py
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Delete old documentation files"`

**Stage 2 Totals**: 11 moved, 6 deleted  
**Est. Time**: 1 hour  
**Status**: [ ] Complete

---

## 🏗️ Stage 3: Move Production Code (Lower Priority, Higher Risk)

### Task 3.1: Move Utilities (5 files) - LOWEST RISK
- [ ] cache_manager.py → src/utils/
- [ ] clear_cache.py → src/utils/
- [ ] clear_stuck_jobs.py → src/utils/
- [ ] fixed_file_utils.py → src/utils/
- [ ] nested_file_utils.py → src/utils/
- [ ] **Test**: ./cslaunch
- [ ] **Test**: Verify no import errors
- [ ] **Commit**: `git commit -m "Move utilities to src/utils"`

### Task 3.2: Move Models (3 files)
- [ ] database_manager.py → src/models/
- [ ] init_database.py → src/models/
- [ ] migrate_citation_databases.py → src/models/
- [ ] **Test**: ./cslaunch
- [ ] **Test**: Verify database operations
- [ ] **Commit**: `git commit -m "Move models to src/models"`

### Task 3.3: Move Integration Code (5 files)
- [ ] api_integration.py → src/integration/
- [ ] citation_integration.py → src/integration/
- [ ] enhanced_api_integration.py → src/integration/
- [ ] final_citation_integration.py → src/integration/
- [ ] final_integration.py → src/integration/
- [ ] **Test**: ./cslaunch
- [ ] **Test**: Verify API integrations
- [ ] **Commit**: `git commit -m "Move integration code"`

### Task 3.4: Move Processors (13 files) - HIGHEST RISK
⚠️ **Test AFTER EACH FILE or small batch**

**Batch 1** (extractors):
- [ ] enhanced_case_extractor.py → src/processors/
- [ ] enhanced_citation_extractor.py → src/processors/
- [ ] enhanced_pdf_citation_extractor.py → src/processors/
- [ ] final_citation_extractor.py → src/processors/
- [ ] **Test**: ./cslaunch + process document

**Batch 2** (processors):
- [ ] a_plus_citation_processor.py → src/processors/
- [ ] enhanced_citation_processor.py → src/processors/
- [ ] document_based_hybrid_processor.py → src/processors/
- [ ] hybrid_citation_processor.py → src/processors/
- [ ] **Test**: ./cslaunch + process document

**Batch 3** (specialized):
- [ ] pdf_citation_extractor.py → src/processors/
- [ ] pdf_processor.py → src/processors/
- [ ] wl_extractor.py → src/processors/
- [ ] modify_processor.py → src/processors/
- [ ] enhanced_unified_citation_processor_standalone.py → src/processors/
- [ ] **Test**: ./cslaunch + process document
- [ ] **Commit**: `git commit -m "Move processors to src/processors"`

**Stage 3 Totals**: 26 moved  
**Est. Time**: 2-3 hours  
**Status**: [ ] Complete

---

## 🔍 Stage 4: Review Unknown Files (Manual Review)

### Task 4.1: Categorize Unknown Files (70 files)
Create spreadsheet/document with:
- [ ] File name
- [ ] Purpose (read first 20 lines)
- [ ] Used? (grep for imports)
- [ ] Decision: DELETE, MOVE, or KEEP
- [ ] Destination (if moving)

**Est. Time**: 1-2 hours

### Task 4.2: Execute Decisions

**Likely DELETE** (~15 files):
- [ ] apply_parallel_enhancements.py
- [ ] apply_parallel_updates.py
- [ ] auto_deprecate_markdown.py
- [ ] deprecate_markdown_files.py
- [ ] fix_syntax_error.py
- [ ] fix_syntax_error_v2.py
- [ ] manual_fix_syntax.py
- [ ] phase2_phase3_deprecation.py
- [ ] prototype_fix69.py
- [ ] remove_disabled_functions.py
- [ ] verify_extracted_data.py
- [ ] [others as identified]
- [ ] **Test**: ./cslaunch after each batch
- [ ] **Commit**: `git commit -m "Delete unused utility files"`

**Move to scripts/** (~20 files):
- [ ] health_check.py → scripts/
- [ ] manage.py → scripts/
- [ ] serve_frontend.py → scripts/
- [ ] wait-for-redis.py → scripts/
- [ ] monitor_health.py → scripts/
- [ ] poll_for_results.py → scripts/
- [ ] poll_task_results.py → scripts/
- [ ] [others as identified]
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Move utility scripts"`

**Move to scripts/analysis/** (~15 files):
- [ ] find_* files
- [ ] get_* files
- [ ] hunt_* files
- [ ] inspect_* files
- [ ] lookup_* files
- [ ] search_* files
- [ ] show_* files
- [ ] trace_* files
- [ ] [others as identified]
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Move analysis scripts"`

**Move to scripts/processing/** (~10 files):
- [ ] process_* files
- [ ] reprocess_* files
- [ ] update_* files
- [ ] [others as identified]
- [ ] **Test**: ./cslaunch
- [ ] **Commit**: `git commit -m "Move processing scripts"`

**Move to src/** (~10 files):
- [ ] Files identified as production code
- [ ] **Test CAREFULLY**: ./cslaunch + full functionality
- [ ] **Commit**: `git commit -m "Move remaining production code"`

**Stage 4 Totals**: ~70 files reviewed and processed  
**Est. Time**: 3-4 hours  
**Status**: [ ] Complete

---

## 🎯 Stage 5: Final Cleanup

### Task 5.1: Delete Old Archived Directories
- [ ] Backup archived/ directory to external storage (optional)
- [ ] Delete archived/
- [ ] Delete archive_deprecated/
- [ ] Delete backup_before_update/
- [ ] Delete archive_temp_files/
- [ ] **Verify**: All code in git history
- [ ] **Commit**: `git commit -m "Delete old archived directories"`

### Task 5.2: Clean Up Backup Directories (After 1 week)
- [ ] Delete backup_reorganization_*
- [ ] Delete backup_phase2_*
- [ ] Delete backup_stage1_*
- [ ] Delete backup_stage2_*
- [ ] Delete backup_stage3_*
- [ ] **Note**: Only after verifying stability for 1 week

### Task 5.3: Update Documentation
- [ ] Update README.md with new structure
- [ ] Create CONTRIBUTING.md with file organization rules
- [ ] Update .gitignore for temp files
- [ ] **Commit**: `git commit -m "Update documentation"`

### Task 5.4: Final Verification
- [ ] Run ./cslaunch - all services operational
- [ ] Process test document - citations working
- [ ] Check all imports - no errors
- [ ] Review directory structure - clean and organized
- [ ] Count files in root - should be 4-10
- [ ] **Commit**: `git commit -m "Final cleanup complete"`

**Stage 5 Totals**: Cleanup complete  
**Est. Time**: 1 hour  
**Status**: [ ] Complete

---

## 📈 Progress Summary

### Overall Statistics
- **Starting files in root**: 157
- **Target files in root**: 4
- **Files to process**: 153

### By Stage
- **Stage 1** (Delete): ~39 files → Est. 118 remaining
- **Stage 2** (Scripts): ~17 files → Est. 101 remaining
- **Stage 3** (Production): ~26 files → Est. 75 remaining
- **Stage 4** (Unknowns): ~70 files → Est. 5 remaining
- **Stage 5** (Final): Cleanup → Est. 4 remaining ✅

### Time Investment
- [x] **Phases 1-2**: 3 hours (DONE)
- [ ] **Stage 1**: 1-2 hours
- [ ] **Stage 2**: 1 hour
- [ ] **Stage 3**: 2-3 hours
- [ ] **Stage 4**: 3-4 hours
- [ ] **Stage 5**: 1 hour
- **Total Remaining**: 8-12 hours

---

## 🎉 Completion Checklist

- [ ] All stages complete
- [ ] Only 4-10 files in root
- [ ] All production code in src/
- [ ] All scripts in scripts/
- [ ] All tests in tests/
- [ ] Application works perfectly
- [ ] No import errors
- [ ] Documentation updated
- [ ] Git committed and pushed
- [ ] **PROJECT COMPLETE!** 🏆

---

## 📝 Notes & Observations

### Issues Encountered
_(Document any problems here)_

### Decisions Made
_(Document important decisions here)_

### Lessons Learned
_(Document insights here)_

---

**Last Updated**: [Date]  
**Current Stage**: Stage 1 (Not started)  
**Next Action**: Run `.\execute_stage1.ps1 -DryRun`
