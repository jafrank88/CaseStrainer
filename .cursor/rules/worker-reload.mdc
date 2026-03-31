---
description: Restart workers after code changes using cslauncher.ps1
alwaysApply: false
globs: src/**/*.py, src/rq_worker*.py, src/rq_worker_pipeline.py
---

# Worker Restart After Code Changes

When you modify backend or worker code (especially `src/rq_worker_pipeline.py`, `src/rq_worker.py`, or any `src/**/*.py` used by RQ workers), **workers must be restarted** to pick up changes. Docker workers do not hot-reload.

## How to Restart

Run the project launcher:

```powershell
.\cslauncher.ps1
```

This script:
- Rebuilds backend + worker containers with latest code
- Restarts workers in correct order (worker-first)
- Clears Python bytecode cache
- Clears Redis and file-based caches
- Optionally rebuilds Vue frontend if changed

## Options

- `.\cslauncher.ps1 -Build:$false` — Skip rebuild (faster, but won't pick up code changes)
- `.\cslauncher.ps1 -SkipHealthCheck` — Skip health check (faster)

## PDF Extraction Unification

File upload (sync), URL/async worker, and test scripts all use `UnifiedTextExtractor` / `extract_text_from_file_unified` for PDFs. This ensures identical citation results regardless of input path. Do not add separate PyPDF2 or other extraction logic to file upload—use the unified extractor.

## When to Run
- `src/rq_worker_pipeline.py`
- `src/rq_worker.py`
- Any module imported by the citation pipeline
