# Code Structure Improvement Analysis

This document summarizes potential improvements in the CaseStrainer codebase structure, based on a static analysis of the backend (`src/`) and frontend (`casestrainer-vue-new/`).

---

## 1. API and routing

### 1.1 Single oversized blueprint

**Issue:** `src/vue_api_endpoints_updated.py` is a single ~4,150-line file containing the entire Vue API (health, analyze, file upload, URL input, task status, progress, verification stream, etc.).

**Impact:** Hard to navigate, review, or test; merge conflicts; slow IDE and tooling.

**Done:** Split by domain into route modules under `src/api/routes/`; the main blueprint is still registered from `vue_api_endpoints_updated.py` (which calls `register_all_routes(vue_api)`). Implemented:

- `src/api/routes/health.py` – health, db_stats
- `src/api/routes/metrics.py` – metrics/summary, metrics dashboard, metrics/daily, metrics/series
- `src/api/routes/progress.py` – analyze/progress, progress-stream, processing_progress
- `src/api/routes/task_status.py` – task_status
- `src/api/routes/verification.py` – verification-stream, verification-status, verification-results

The `/analyze` POST handler and its helpers remain in `vue_api_endpoints_updated.py` (single large module) for now.

---

## 2. Duplicate and dead code paths

### 2.1 Two “process citation task” implementations

**Issue:** There are two separate implementations for “process a citation task”:

| Location | Function | Used by |
|----------|----------|---------|
| `src/rq_worker.py` | `process_citation_task_direct` | Registered with RQ; delegates to `run_citation_task` |
| `src/rq_worker_pipeline.py` | `run_citation_task` | Called by the above; uses `CitationService` / `DockerOptimizedProcessor` |
| `src/progress_manager.py` | `process_citation_task_direct` | **Deprecated.** Thin wrapper to `run_citation_task`; not used by API/RQ. |

The API and RQ enqueue `src.rq_worker.process_citation_task_direct`, which calls `run_citation_task`. The `process_citation_task_direct` in `progress_manager.py` is now a thin deprecated wrapper that delegates to `run_citation_task`; the API and RQ use only `src.rq_worker.process_citation_task_direct`.

**Recommendation:**

- Callers should use `src.rq_worker.process_citation_task_direct` or `run_citation_task` directly.
- The progress_manager wrapper will be removed in a later release.

### 2.2 Two pipeline stacks for “full” processing

**Issue:** Two different pipelines can run “full” citation processing:

1. **RQ path (current production for file/URL):**  
   `run_citation_task` → `CitationService` → `DockerOptimizedProcessor` (Redis-distributed processing).

2. **Sync path:**  
   `process_citations_unified()` in `unified_processing_pipeline.py` (extraction → clustering → verification in-process). The deprecated `extract_citations_with_clustering` in `citation_extraction_endpoint.py` now raises only and is not used.

Used by: `unified_input_processor` (fallback and sync), health checks, and sync `/analyze` branch. All use `process_citations_unified`.

**Recommendation:** Canonical paths are documented in `docs/PIPELINE_ENTRY_POINTS.md`: async = RQ + `run_citation_task`; sync = `process_citations_unified`.

---

## 3. Mismatch and cluster-flag logic

### 3.1 Scattered `has_name_mismatch` / `has_date_mismatch` logic

**Issue:** Cluster-level `has_name_mismatch` and `has_date_mismatch` are computed in many places:

- `src/rq_worker_pipeline.py` (recompute after fixes)
- `src/utils/post_verify_split.py` (after splits)
- `src/unified_citation_processor_v2.py` (date mismatch, clear invalid flags)
- `src/unified_processing_pipeline.py` (multiple spots, including year rules)
- `src/citation_extraction_endpoint.py` (annotate)
- `src/vue_api_endpoints_updated.py` (equiv logic, clear flags)
- `src/utils/mismatch_utils.py` (annotate)

**Impact:** Same conceptual logic lives in several modules; rule changes (e.g. year tolerance) require updates in multiple files; risk of inconsistent behavior between API and worker.

**Recommendation:** Centralize in one place:

- Prefer `src/utils/mismatch_utils.py` as the single place for “given citations/cluster, compute and set `has_name_mismatch` / `has_date_mismatch` (and optionally mismatch_indices).”
- Have `rq_worker_pipeline`, `unified_processing_pipeline`, `citation_extraction_endpoint`, and `vue_api_endpoints_updated` call into that utility after building/updating clusters, instead of reimplementing rules.
- Document the intended rules (e.g. year thresholds, equivalence) in `mismatch_utils` and keep schema in `src/schemas/cluster.py`.

---

## 4. Name normalization and token logic

### 4.1 Duplicate `_normalize_name_tokens` implementations

**Issue:** Two almost identical implementations:

- `src/citation_extraction_endpoint.py` – `_normalize_name_tokens` (and related name logic)
- `src/utils/mismatch_utils.py` – `_normalize_name_tokens` (and `_name_similarity`, `_names_equivalent`)

The citation_extraction_endpoint version has a larger replacement map; the logic is the same idea.

**Recommendation:** Keep a single implementation in `mismatch_utils.py` (or a shared `src/utils/name_normalization.py`). Have `citation_extraction_endpoint` import and use it (e.g. `from src.utils.mismatch_utils import _normalize_name_tokens` or a small public API) and remove the duplicate. This supports the broader goal of one place for mismatch/name logic.

---

## 5. Progress and task orchestration

### 5.1 Progress manager file size and responsibilities

**Issue:** `src/progress_manager.py` is very large (~2,500+ lines) and mixes:

- Progress tracking (SSE, WebSocket, Redis sync)
- `process_citation_task_direct` (duplicate, unused by RQ)
- URL fetching and preprocessing (`fetch_url_content`, `preprocess_extracted_text`)
- PDF extraction helpers

**Recommendation:**

- Split into focused modules, e.g.:
  - `src/progress/` or keep `progress_manager.py` for “progress tracking only” (SSE, WebSocket, Redis, progress trackers).
  - Move URL fetching and text preprocessing to something like `src/input_fetchers.py` or under `src/api/` if they are only used by API handlers.
  - Remove or relocate the duplicate `process_citation_task_direct` as in §2.1.
- This keeps progress semantics in one place and makes URL/PDF logic easier to reuse and test.

---

## 6. Entry points and “unified” pipelines

### 6.1 Many “unified” or “main” entry points

**Issue:** Multiple modules present themselves as the main or unified entry:

- `unified_processing_pipeline.py` – `process_citations_unified`, `UnifiedProcessingPipeline`
- `unified_input_processor.py` – `UnifiedInputProcessor`, `process_any_input`
- `unified_citation_processor_v2.py` – `UnifiedCitationProcessorV2`, `process_text`
- `citation_extraction_endpoint.py` – `extract_citations_production`, `extract_citations_with_clustering`

Docstrings and comments indicate intended replacement of older paths, but all remain in use from different call sites.

**Recommendation:**

- Pick one “canonical” entry for sync processing (e.g. `process_citations_unified` or `extract_citations_with_clustering`) and document it in a single place (e.g. `docs/PIPELINE_ENTRY_POINTS.md`).
- Map other entry points to that one (wrapper or thin adapter) so behavior and fixes live in one pipeline. Gradually migrate callers to the canonical entry and deprecate the rest.
- Keep RQ path (`run_citation_task`) as the single async entry and have it call the same core pipeline (possibly via CitationService/DockerOptimizedProcessor) so sync and async share logic.

---

## 7. Frontend

### 7.1 Large single component

**Issue:** `casestrainer-vue-new/src/components/CitationResults.vue` is a large component (1,200+ lines) handling:

- Cluster grouping (verified, unverified, mismatch, other, etc.)
- Display helpers (names, dates, URLs, badges)
- Export and filters
- Many computed properties and inline logic

**Recommendation:**

- Extract composables (e.g. `useCitationClusters`, `useClusterDisplay`) for grouping and “effectively verified” / URL logic.
- Extract presentational subcomponents (e.g. `ClusterCard`, `CitationList`, `VerificationBadge`) and keep `CitationResults.vue` as orchestration and layout.
- This will improve readability and make cluster/verification rules easier to unit test.

### 7.2 API and env

**Issue:** API base URL and endpoints may be hardcoded or repeated (e.g. `/casestrainer/api`, `/analyze`, `/task_status/`).

**Recommendation:** Use a single API module (e.g. `api/casestrainer.js` or `api/index.js`) that reads base URL from env and exports endpoint builders or constants. Use it everywhere instead of string literals.

---

## 8. Testing and scripts at repo root

**Issue:** Many loose scripts at repo root (`check_*.py`, `debug_*.py`, `read_*.py`, `test_*.py`, etc.) that look like one-off or legacy tools. They make the root noisy and blur the line between tests and ad-hoc scripts.

**Recommendation:**

- Move one-off/debug scripts to something like `scripts/debug/` or `scripts/adhoc/` and add a short README.
- Keep only entry points (e.g. `run_worker`, app entry) and a small set of “blessed” scripts at root.
- Use a clear test layout (e.g. `tests/` with `conftest.py` and structured test modules) and run real tests via pytest; avoid naming one-off scripts like tests unless they are tests.

---

## 9. Suggested priority order

1. **High:** Centralize cluster mismatch flags in `mismatch_utils` and have all pipelines call it (§3).
2. **High:** Remove or deprecate duplicate `process_citation_task_direct` in `progress_manager` and document the single RQ path (§2.1).
3. **Medium:** Split `vue_api_endpoints_updated.py` into domain route modules (§1.1).
4. **Medium:** Deduplicate name normalization and keep one implementation in `mismatch_utils` (§4).
5. **Medium:** Split `progress_manager.py` and move URL/preprocessing to a dedicated module (§5.1).
6. **Lower:** Unify pipeline entry points and document canonical sync/async paths (§2.2, §6.1).
7. **Lower:** Refactor `CitationResults.vue` with composables and subcomponents (§7.1); consolidate API base URL (§7.2); tidy root scripts (§8).

---

## 10. Quick reference: who calls what

| Caller | Calls | Purpose |
|--------|--------|--------|
| RQ (enqueued job) | `src.rq_worker.process_citation_task_direct` | File/URL async processing |
| `rq_worker.process_citation_task_direct` | `run_citation_task` (rq_worker_pipeline) | Actual task execution |
| `run_citation_task` | `CitationService` / `DockerOptimizedProcessor` | Extraction + clustering + verification in worker |
| `unified_input_processor` (fallback/sync) | `process_citations_unified` | Sync/fallback path |
| `progress_manager.process_citation_task_direct` | **Deprecated.** Thin wrapper to `run_citation_task`; not used by API/RQ. | Backward compatibility only |
| Health checks | `process_citations_unified` | Smoke test |
| `vue_api` (sync analyze) | `UnifiedInputProcessor` → `process_citations_unified` | Sync analyze requests |

This table is aligned with `docs/PIPELINE_ENTRY_POINTS.md`; update both when entry points change.
