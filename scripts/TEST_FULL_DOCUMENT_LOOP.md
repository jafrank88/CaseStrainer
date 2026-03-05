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
