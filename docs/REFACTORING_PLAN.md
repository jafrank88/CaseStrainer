# Codebase Duplication & Refactoring Plan

This plan addresses the duplication and structural issues identified in the CaseStrainer codebase. It is ordered by priority and dependency so that high-impact, low-risk work comes first and later phases build on a cleaner base.

---

## Implementation Status (as of Phase 5)

| Phase | Status | Notes |
|-------|--------|--------|
| **1** | Done | Case name utils in `src/utils/case_name_utils.py`; extraction re-exports; .gitignore updated; plan corrected (app_final_vue in use). |
| **2** | Done | Single verification path via `src.verification`; `verification_services.py` removed; all callers use `src.verification`; `get_master_verifier` added. |
| **3** | Done | Extraction single path: `app_final_vue`, `case_name_extraction_core`, health/citation/vue endpoints use `src.extraction`; `extract_case_name_from_strict_context` and `get_master_extractor` re-exported; `extract_citations_unified` import fixed. |
| **4** | Done | `BaseURLVerifier` in `src/verification/sources.py`; Justia, Cornell LII, OpenJurist refactored to extend it. |
| **5** | In progress | `src/rq_worker_helpers.py` (~190 lines). **Done:** `src/utils/response_finalize.py` — shared merge-by-URL, re-finalize, dedupe, and optional `display_citations` rebuild used by `vue_api_endpoints_updated` and `rq_worker_pipeline`. **Remaining:** split `unified_citation_processor_v2`, thin `vue_api_endpoints_updated` further (move `_analyze_impl` into services). |

---

## Summary of Verified Findings

| Area | Claim | Verified |
|------|--------|----------|
| **Verification layer** | 3 parallel systems | **Yes.** `verification_manager.py` (Redis status API) is used in `rq_worker.py`, `vue_api_endpoints_updated.py` (12+ imports), `unified_input_processor.py`, `canonical_metadata.py`. `async_verification_worker.py` is the RQ task for verification; it imports `UnifiedVerificationMaster` from `unified_verification_master`. `verification_services.py` is imported only in `unified_citation_processor_v2.py` (CourtListenerService). |
| **Case name extraction** | 6+ implementations, 4-layer indirection | **Yes.** `case_name_extraction_core` → `unified_case_name_extractor_v2` → `utils/unified_case_name_extractor` → `utils/strict_context_isolator`. Modular path: `unified_case_extraction_master` (shim) → `src/extraction/`. |
| **Utility duplication** | clean_case_name (7), is_valid_case_name (4) | **Yes.** Multiple copies in `case_name_extraction_core`, `unified_case_name_extractor_v2`, `extraction/utils.py`, `clustering/utils.py`, `models.py`, `toa_utils_consolidated`, etc. |
| **Dead/superseded files** | Shims, backups, app_final_vue | **Corrected.** Shims confirmed. `.backup` already in .gitignore; no backup files in repo. **`app_final_vue.py` is the main Flask app** (docker-compose, wsgi.py, manage.py, scripts) — **do not remove**. Debug `.txt` files in `src/` are largely covered by existing .gitignore patterns. |
| **Verifier boilerplate** | Justia/Cornell/OpenJurist ~80% same | **Yes.** `sources.py` uses shared `URLBuilder`, `HTMLExtractor`, `NameValidator`, `HTTPClient` from `fallback_verification_utils`; a `BaseURLVerifier` would reduce duplication. |

**Important distinction:** `VerificationManager` is **not** the same as `UnifiedVerificationMaster`.  
- **VerificationManager** = Redis-backed status/progress API (`get_verification_status`, `get_verification_results`, `register_verification`, `update_progress`). Used by the API layer so the frontend can poll progress.  
- **UnifiedVerificationMaster** = actual verification engine (CourtListener, fallbacks, batch).  
So “consolidation” means: (1) keep a single status/progress layer (optionally under `src/verification/`), and (2) use only `src/verification` for all verification logic; remove duplicate logic from `verification_services.py` and ensure `async_verification_worker` and pipelines use the modular package only.

---

## Phase 1: Quick Wins (Low Risk)

**Goal:** Remove dead weight and confirm ownership of single-purpose modules. No behavioral change.

### 1.1 Delete backup and unused files

- **Actions:**
  - **Done:** `.gitignore` already includes `*.backup`; no backup files found in repo.
  - **Do not remove `app_final_vue.py`** — it is the main Flask app (docker-compose, wsgi.py, manage.py, run_app, start_backend, etc.).
  - Debug/test `.txt` files in `src/` are mostly covered by existing patterns (`test_*.txt`, `*_debug*.txt`, etc.). Add `src/diag*.txt` to `.gitignore` if such files appear.
- **Check:** Full test suite and a quick manual run of the main pipeline (file upload → analyze → results).

### 1.2 Centralize utility functions (single source of truth)

- **Goal:** One implementation each for `clean_case_name`, `is_valid_case_name`, and a single place for citation normalization and year/date extraction where possible.
- **Actions:**
  - **Case name utils:** Create `src/utils/case_name_utils.py` that provides:
    - `clean_case_name(name: str) -> str`
    - `is_valid_case_name(name: str) -> bool`
  - Implement once (e.g. adopt the logic from `src/extraction/utils.py` and `src/extraction/validation.py`, which are already used by the extraction package).
  - **Date utils:** Ensure `src/utils/date_utils.py` (or a single module) is the only place for `extract_year` / `extract_date`-style helpers; add if missing. Plan to migrate callers in a later phase so Phase 1 stays small.
  - **Citation utils:** Create `src/utils/citation_utils.py` for `normalize_citation` / `clean_citation` / `parse_citation` (one canonical implementation). Migrate callers in a later phase.
- **Migration strategy:** In Phase 1, only add the new modules and use them from **one** high-traffic caller (e.g. `extraction/utils.py` and `extraction/validation.py`). Leave other call sites for Phase 2 to avoid a large blast radius.
- **Check:** Unit tests for the new util functions; existing extraction tests still pass.

---

## Phase 2: Verification Layer Consolidation (High Priority)

**Goal:** Single verification implementation and a clear split between “status/progress” and “verification logic.” No duplicate verification code paths.

### 2.1 Treat `src/verification` as the only verification implementation

- **Current state:**
  - Actual verification: `src/verification/` (UnifiedVerificationMaster) + compatibility shim `unified_verification_master.py`.
  - Status/progress: `verification_manager.py` (VerificationManager) used by API and RQ worker.
  - Legacy: `verification_services.py` (CourtListenerService) only in `unified_citation_processor_v2.py`; `async_verification_worker.py` already uses `unified_verification_master` → `UnifiedVerificationMaster`.
- **Actions:**
  1. **Expose missing symbols from `src.verification`:**
     - Export from `src.verification` (and re-export from shim if needed during transition):
       - `apply_known_federal_to_citation_objects`, `apply_last_mile_cluster_display_sync` from `result_processing.py`
       - `_normalize_citation_for_known_lookup` (or a public wrapper) from `known_citations.py`
     - Add `get_master_verifier()` in `src/verification` (e.g. in `master.py` or `__init__.py`) that returns a shared or new `UnifiedVerificationMaster` instance. Update `citation_extraction_endpoint.py` to import from `src.verification` instead of the shim.
  2. **Replace `verification_services` usage:** In `unified_citation_processor_v2.py`, replace `CourtListenerService` from `verification_services` with the CourtListener path from `src.verification` (e.g. `CourtListenerVerifier` or the batch/fallback flow). Remove `verification_services.py` once no longer imported.
  3. **Keep VerificationManager for status only:** Do **not** delete `verification_manager.py` yet. It is the Redis-backed status/progress API. Optionally move it to `src/verification/status.py` (or `progress.py`) and re-export `VerificationManager` from `src.verification` so the API and RQ worker can import from one place. Alternatively, leave it as `src/verification_manager.py` but document that it is the “status/progress” layer and that all verification logic lives in `src/verification`.
  4. **Ensure async worker uses only `src.verification`:** `async_verification_worker.py` already uses `UnifiedVerificationMaster` via the shim. Switch its imports to `src.verification` directly and remove the shim from the import path.
  5. **Update all call sites** that still import from `unified_verification_master` to import from `src.verification` (and from `src.verification_manager` only for VerificationManager if kept separate). Then deprecate or remove the shim `unified_verification_master.py`.

### 2.2 Remove legacy verification modules

- After 2.1:
  - Delete or archive `verification_services.py`.
  - If `async_verification_worker.py` can be inlined into a single entrypoint that uses only `src.verification` and the RQ job is just a thin wrapper, consider folding it into a module under `src/verification/` (e.g. `async_worker.py`) so there is one verification package. Otherwise keep the file but ensure it has no imports from the deleted modules.
- **Check:** Full regression (file + paste + URL analyze); status polling and result retrieval in the UI; no remaining imports of `verification_services` or the old shim except for optional compatibility.

---

## Phase 3: Case Name Extraction Simplification (Medium Priority)

**Goal:** One clear path for “extract case name (and date)” so fixes and improvements happen in one place.

### 3.1 Single entrypoint for extraction

- **Current chain:** `case_name_extraction_core` → `unified_case_name_extractor_v2` → `utils/unified_case_name_extractor` → `utils/strict_context_isolator`.
- **Target:** All callers use `src/extraction` (e.g. `extract_case_name_and_date_unified_master` or a new single function) which internally uses `strict_context_isolator` (or equivalent) as the implementation.
- **Actions:**
  1. List all call sites of `extract_case_name`, `case_name_extraction_core`, and `unified_case_name_extractor_v2` (and the utils path).
  2. Change each to call the extraction package API only (e.g. `from src.extraction import extract_case_name_and_date_unified_master` or `from src.unified_case_extraction_master import ...` during transition).
  3. Make `src/extraction` (and optionally `utils/strict_context_isolator`) the only implementation; remove or thin the wrapper layers so that `case_name_extraction_core` and `unified_case_name_extractor_v2` become thin re-exports or are removed and callers updated.
  4. Once no code path uses the old chain, delete or archive the old extraction monoliths and keep only the shim if needed for compatibility, or remove the shim and use `src.extraction` everywhere.

### 3.2 Utility consolidation (continued)

- Migrate all remaining callers of `clean_case_name` and `is_valid_case_name` to `src/utils/case_name_utils.py` (from Phase 1).
- Migrate `extract_year` / `extract_date` callers to the single date util module.
- Migrate citation normalization callers to `src/utils/citation_utils.py`.

---

## Phase 4: Verifier Boilerplate (Medium Priority)

**Goal:** Less duplication and clearer behavior in web verifiers (Justia, Cornell LII, OpenJurist).

### 4.1 BaseURLVerifier in `src/verification/sources.py`

- **Actions:**
  1. Add a `BaseURLVerifier` (or similar) that implements the common flow: build URL (abstract or via strategy), fetch page, extract name (e.g. via HTMLExtractor), validate (e.g. NameValidator), return result dict.
  2. Refactor `JustiaVerifier`, `CornellLIIVerifier`, and `OpenJuristVerifier` to extend it and override only URL building and any source-specific extraction/validation.
  3. Add unit tests for the base and one subclass to avoid regressions.

---

## Phase 5: Break Up Monoliths (Lower Priority, High Effort)

**Goal:** Reduce file size and mix of concerns so that changes are localized and reviewable.

### 5.0 Helpers extracted (done)

- **`src/rq_worker_helpers.py`** created with: `_force_release_memory`, `STATE_REPORTERS`, `CASE_HISTORY_SIGNALS`, `_get_citation_state`, `_citations_compatible_for_parallel`, `_has_case_history_signal_between`, `_extract_reporter_type_simple`, `_are_parallel_reporter_types`. `rq_worker.py` imports from it; RQ entry points unchanged.

### 5.1 Target files (confirmed large)

- `rq_worker.py` (~215KB after helper extract) — still holds `_process_citation_task_internal` (~2,800 lines), `verify_citations_enhanced`, `RobustWorker`, `process_citation_task_async`, `main`.
- `unified_citation_processor_v2.py` (~259KB) — extraction, verification, clustering, formatting.
- `vue_api_endpoints_updated.py` (~197KB) — many endpoints and VerificationManager calls.
- `progress_manager.py`, `unified_processing_pipeline.py`, `unified_case_name_extractor_v2.py` — also large.

### 5.2 Approach (remaining)

- **rq_worker.py:** **Done.** `_process_citation_task_internal` extracted to `src/rq_worker_pipeline.run_citation_task(...)`. rq_worker only wires RQ and delegates; pipeline holds the full task logic (~2885 lines).
- **unified_citation_processor_v2.py:** Extract into submodules under e.g. `citation_processing/` (or under `src/`): extraction step, verification step, clustering step, formatting step. Main module becomes thin orchestrator.
- **vue_api_endpoints_updated.py:** Group routes by domain (analyze, task_status, verification, health) into separate modules; register blueprints from app or main routes file.

---

## Priority Overview

| Priority | Phase | Focus |
|----------|--------|--------|
| **HIGH** | 1.1 | Delete dead/backup/unused files |
| **HIGH** | 2 | Verification layer: single implementation, remove verification_services, optional move of VerificationManager into src/verification |
| **MEDIUM** | 1.2, 3 | Utility consolidation; case name extraction single path |
| **MEDIUM** | 4 | BaseURLVerifier and source verifier dedup |
| **LOW** | 5 | Split rq_worker, unified_citation_processor_v2, vue_api_endpoints |

---

## Dependency Order

1. **Phase 1** can start immediately (no dependency on other phases).
2. **Phase 2** can start in parallel with Phase 1; complete Phase 2 before relying on a single verification path when splitting monoliths.
3. **Phase 3** (extraction) is better after Phase 2 so that verification and extraction aren’t both in flux.
4. **Phase 4** can follow Phase 2 (verification package is stable).
5. **Phase 5** should follow Phases 1–2 and ideally 3.

---

## Testing and Rollback

- **Per phase:** Run full test suite; run at least one full flow (file upload → analyze → citation/verification results) and confirm status polling and result display.
- **Rollback:** Each phase should be a small set of commits (e.g. “Add case_name_utils and switch extraction to it” vs “Delete 10 files”). Prefer feature flags or re-exports over big-bang deletions so rollback is revert-by-commit.

---

## Optional: Compatibility Shims

- The shims `unified_verification_master.py`, `unified_case_extraction_master.py`, and `unified_clustering_master.py` are useful during migration. Plan:
  - Once every caller uses `src.verification` directly, remove or reduce `unified_verification_master.py`.
  - Same for extraction and clustering once callers use `src.extraction` and `src.clustering` directly.
- Keep shims until grep shows no remaining imports from the shim module names.

---

## Remaining Steps — Re-evaluation

After Phases 1–4 and Phase 5 (helpers), the following steps would add the most value for the effort.

### High value, lower effort

1. **Migrate remaining `clean_case_name` / `is_valid_case_name` callers**  
   **Done.** `clustering/utils.py`, `toa_utils_consolidated.py`, `unified_case_name_extractor_v2.py`, and `case_name_extraction_core.py` now delegate to `src.utils.case_name_utils`. `models.py` was left as-is (its `_clean_case_name` handles citation-object contamination, not generic case name cleaning).

2. **Remove or thin compatibility shims when safe**  
   Once no (or minimal) code imports from `unified_verification_master` or `unified_case_extraction_master`, remove the shim files or reduce them to a single re-export line. Run a repo-wide grep for those module names before deleting.

3. **Single date util and citation util**  
   **Done (date); citation facade in place.** `src/utils/date_utils.py` is the single source for year/date. Callers migrated: `citation_extraction_endpoint.py` (uses `extract_year_value`), `mismatch_utils.py` (`_extract_year` delegates to `extract_year_value`), `unified_processing_pipeline.py` (local helpers replaced with `extract_year_value` + `extract_year_from_citation`), `unified_citation_processor_v2.py` (inline `_extract_year` replaced with `extract_year_value`). `src/utils/citation_utils.py` re-exports `normalize_citation` and `generate_citation_variants`; migrate remaining citation_utils_consolidated importers over time.

### Medium value, higher effort

4. **Extract `_process_citation_task_internal` from rq_worker**  
   **Done.** Logic moved to `src/rq_worker_pipeline.py` as `run_citation_task(task_id, input_type, input_data, logger=None)`. `rq_worker.py` keeps a thin `_process_citation_task_internal` that delegates to `run_citation_task(..., logger=logger)`. ~2885 lines removed from rq_worker. Run full pipeline tests to confirm.

5. **Split vue_api_endpoints_updated by domain**  
   Create e.g. `vue_api/analyze.py`, `vue_api/task_status.py`, `vue_api/verification.py`, register blueprints from one place. Reduces merge conflicts and speeds up navigation.

### Lower priority

6. **Split unified_citation_processor_v2**  
   Largest file; splitting into `citation_processing/extraction.py`, `verification.py`, `clustering.py`, `formatting.py` is a multi-day refactor. Do after rq_worker and vue_api are split so the citation pipeline is the only big touch.

7. **Move VerificationManager into src/verification**  
   Optional: put `verification_manager.py` logic into `src/verification/status.py` and re-export `VerificationManager` from `src.verification` so all verification-related imports live under one package.

---

## Document history

- Created from codebase duplication analysis; verified via grep and file reads.
- Key correction: VerificationManager = status/progress API; UnifiedVerificationMaster = verification engine. Both are kept; only duplicate *logic* (verification_services, multiple verification code paths) is removed.
- Phases 1–4 and Phase 5 (helpers) implemented; plan updated with status table and “Remaining Steps — Re-evaluation”.
