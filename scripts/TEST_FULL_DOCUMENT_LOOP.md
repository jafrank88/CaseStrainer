# Test full document until it completes

Use this loop after code changes to verification/batch or workers until the 1028814.pdf (or your test PDF) runs to completion.

## 1. Rebuild and restart workers

From the project root (Windows):

```powershell
.\cslauncher.ps1
```

Wait ~2 minutes for workers to be ready.

## 2. Run the test script

**Local (Docker on same machine):**

```powershell
python scripts/test_full_document_flow.py
# Or with explicit PDF:
python scripts/test_full_document_flow.py D:\path\to\1028814.pdf
```

**Production (e.g. wolf.law.uw.edu):**

```powershell
$env:BASE_URL="https://wolf.law.uw.edu/casestrainer/api"
python scripts/test_full_document_flow.py D:\dev\casestrainer\1028814.pdf
```

The script uploads the PDF, polls task status every 2.5s for up to 15 minutes, and prints progress. It exits 0 on success, 1 on failure/timeout.

## 3. If it times out or fails

- Note the **last progress message** (e.g. "Processing 100 citations... (10 processed)").
- Check worker logs for the task and any BATCH/timeout lines:

```powershell
docker logs casestrainer-rqworker1-prod --tail 150 2>&1 | Select-String "BATCH|timeout|1bb78cf8"
# Repeat for rqworker2-prod through rqworker6-prod, or grep for your task_id
```

- Share the script output and relevant log snippets so we can adjust timeouts or batch logic.
- After code changes, run **cslauncher** again (step 1), then re-run the script (step 2).

## 4. Success

When the script prints:

```
SUCCESS: N citations, M clusters, V verified
```

the pipeline is getting through the entire document (extraction + verification).

---

## Stuck at "10 processed" on production (e.g. wolf)?

If the UI stays at "Processing 100 citations... (10 processed)" for minutes:

1. **Deploy the latest code on the server.** The backend that runs jobs is on the server (e.g. wolf). Run `git pull` and rebuild/restart workers **on that machine** (see "Deploying to wolf" below). Without the O(n) normalization and batch timeout fixes, the worker can hang in extraction or verification.

2. **Pipeline timeout:** The worker will stop after **5 minutes** by default (`PIPELINE_TIMEOUT_SECONDS=300`). You’ll see a "Processing timed out" error. For large documents, set on the server: `PIPELINE_TIMEOUT_SECONDS=600` (or in docker-compose/env).

3. **Check worker logs on the server** (see "If a job still looks stuck on wolf" below) to see whether it’s stuck in extraction or verification.

---

## Deploying to wolf (production)

**Code that runs is on the server.** If you run `cslauncher` only on your dev machine, wolf.law.uw.edu still runs whatever is deployed there. To get the latest fixes on wolf:

1. **On the wolf server:** pull the repo and rebuild/restart so workers get the new code, e.g.:
   ```powershell
   cd /path/to/casestrainer   # or your deploy path on wolf
   git pull
   .\cslauncher.ps1
   ```
   (Use whatever deploy process you use on wolf: docker-compose, systemd, etc.)

2. **Confirm workers have the fix:** On the server (PowerShell or bash):
   ```bash
   docker exec casestrainer-rqworker1-prod grep -n "_digit_run_max\|Cap run at 30" /app/src/unified_citation_processor_v2.py
   ```
   You should see the 0a bounded digit-run line. Repeat for worker2–6 if needed.

3. **If a job still looks stuck on wolf:** Find the task ID (from the UI or test script), then on the wolf server (bash):
   ```bash
   # Replace TASK_ID with the stuck task id (e.g. 3840e710-2974-4464-9def-2d2fefb0fae4)
   TID="TASK_ID"
   for i in 1 2 3 4 5 6; do echo "=== worker$i ==="; docker logs casestrainer-rqworker${i}-prod --tail 200 2>&1 | grep "$TID" || true; done
   ```
   See which worker shows the task, then for that worker (e.g. N=3):
   ```bash
   docker logs casestrainer-rqworkerN-prod --tail 300 2>&1 | grep -E "UNIFIED_EXTRACTION|BATCH|Step 1|Phase 4.75|timed out"
   ```
   - If you see "Text normalized" but never "Step 1: Enhanced regex extraction" → stuck in full-document normalization.
   - If you see "Step 1" and "Phase 4.75" but progress stays at 10 → stuck in verification (batch timeout or progress callback).
   - Share the last few matching lines to narrow the fix.
