# Async worker code path and clustering

## Do workers use the same code as the repo?

**Yes.** Async tasks (file upload, URL, or text that return a `task_id` and are polled) are handled by the RQ worker, which runs the **same pipeline** as sync processing.

### Flow

1. **API** receives request → may enqueue RQ job (async) or call `CitationService` / `UnifiedInputProcessor` (sync).
2. **RQ worker** (e.g. `rq_worker_pipeline.run_citation_task`) runs the job.
3. Worker calls **`process_citations_unified`** from `src.unified_processing_pipeline` (same as sync).
4. Pipeline uses **`cluster_citations_optimized`** from `src.unified_clustering_master_optimized`, which:
   - Groups by **canonical_url** when present (keeps parallel citations together).
   - Uses **canonical_name** when extracted name is N/A (e.g. Kustura 233 P.3d 853).
   - Uses **`citation_conflicts_with_group`** from `src.utils.cluster_filter` (same reporter + different volume = conflict except same canonical_url / same canonical case).
   - Uses **`names_are_same_case`** from `src.utils.same_case` (generic plaintiff "State" requires defendant match).

So **async and sync both use**:

- `unified_processing_pipeline.process_citations_unified`
- `unified_clustering_master_optimized.cluster_citations_minimal`
- `utils.cluster_filter.citation_conflicts_with_group`
- `utils.same_case.names_are_same_case`

## Why do I still see old behavior (Kustura split, Perry mixed, etc.)?

If the repo has the fixes but you still see:

- **Kustura** as two cards (169 Wn.2d / 169 Wash. 2d vs 233 P.3d 853),
- **Perry v. Beverage** with 209 P. 1102 and 214 P. 146 on the same card,
- **State v. Kier** and **State v. Stalker** merged,

then the **running worker (and app) process is still using an older version of the code**.

### What to do

1. **Redeploy / restart**
   - Restart the RQ worker process(es) so they load the updated code.
   - If you deploy from git (e.g. on wolf.law.uw.edu), pull the latest, then restart the app and workers (e.g. `systemctl restart rq-worker` or your process manager).
2. **Confirm code on the server**
   - On the server, `git log -1 --oneline` and `git status` to ensure the repo is at the commit that includes the clustering/same_case/cluster_filter fixes.
3. **No separate "worker codebase"**
   - There is no separate worker codebase; both sync and async use the same `src` modules. So once the server has the latest code and workers are restarted, async results will match the fixed behavior.

## Verifying which code ran

The pipeline response includes **`metadata.clustering_version`** (e.g. `"2026-03-v2"`). The async worker now puts this in the result metadata so it appears in the task_status API response. After redeploying:

1. Run a job and open the task result (or poll `GET /api/task_status/<task_id>`).
2. Check **`metadata.clustering_version`** in the JSON response.
3. If you see `"2026-03-v2"` (or the current `CLUSTERING_VERSION` in `unified_clustering_master_optimized.py`), the worker is running the updated clustering code.
4. If you see `"fallback"` or `"unknown"`, the optimized module did not load or an old build is still running.

## Is the issue backend or display?

All clustering and sectioning (Name Differences, Date Differences) is done in the backend. The UI shows **one card per cluster**: the "67 Cases Found" count is `clusters.length` from the API.

To confirm from the JSON:

1. **GET** the task result (e.g. `GET /api/task_status/<task_id>` when status is completed).
2. Inspect **`clusters`**:
   - **Length** = number of case cards. If you see 67, the backend produced 67 clusters.
   - **Kustura**: search for clusters whose `cluster_case_name` or citations mention "Kustura". If there are **two** such clusters (one with 169 Wn.2d 81 / 169 Wash. 2d 81, one with 233 P.3d 853), the backend is still producing split Kustura clusters (old logic or old deploy). If there is **one** cluster with all three citations, clustering is correct.
   - **Perry v. Beverage**: if one cluster has citations 121 Wash. 652..., 209 P. 1102, and 214 P. 146, the backend merged three different cases into one (old conflict logic). Correct behavior is separate clusters for distinct reporters/volumes unless they share the same `canonical_url`.
3. **`cluster_sections`** (e.g. `case_mismatch`, `date_mismatch`) are computed from these clusters in `compute_cluster_sections()`; they do not create or split clusters.

So if the **JSON** has 67 clusters and split Kustura / merged Perry, the problem is **backend** (clustering/conflict logic or workers not restarted). If the JSON had one Kustura cluster and separate Perry clusters but the UI showed 67 and wrong cards, the problem would be **display**—but the display is a direct reflection of the backend `clusters` array.
