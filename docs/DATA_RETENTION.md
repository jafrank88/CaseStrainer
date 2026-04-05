# Data retention and privacy

This document summarizes what CaseStrainer keeps by default and how operators can tighten retention.

## Overview

- **Async jobs** store progress and results in **Redis** (and RQ metadata). Default time-to-live is **one hour** unless you override it.
- **Uploaded files** for async processing can be **deleted on the worker** after the job finishes (success or failure), by default.
- **Full API response logging** to disk is **off by default**; enable only when you explicitly need audit-style payload logs.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATA_RETENTION_ASYNC_SECONDS` | `3600` | TTL (seconds) for Redis keys used for async results, progress, and verification status/result mirrors. Clamped to **60–604800** (1 minute to 7 days). |
| `UPLOAD_DELETE_AFTER_PROCESSING` | `true` | When `true`, the worker attempts to remove the uploaded file path after an async **file** job completes. Set to `false` if you rely on keeping uploads on disk for retries or forensics. |
| `CASESTRAINER_LOG_FULL_API_RESPONSES` | `false` | When `true`, successful analyze responses may be appended as JSON to `/app/logs/frontend_api_results.log` (when `/app/logs` exists). **Privacy risk** if document or citation content appears in responses. |

Copy these into your `.env` as needed; see the repository `.env.example`.

## What uses the async retention TTL

The same configured TTL is applied consistently to:

- RQ job `result_ttl` / `failure_ttl` (and related queue TTL where used)
- Keys such as `task_result:{task_id}`, `rq:job:{task_id}:result`, `progress:{task_id}`, and verification-related Redis keys written by the pipeline

**Job execution timeout** (how long a worker may run a single job) is separate from Redis TTL and is not changed by `DATA_RETENTION_ASYNC_SECONDS`.

## Third-party services

Verification may call external APIs (for example CourtListener or LangSearch, when configured). Those providers have their own retention and privacy policies; they do not receive Redis keys from CaseStrainer, but they receive the request payloads your deployment sends for verification.

## Source of truth

Implementation lives in `src/config.py` (`DATA_RETENTION_ASYNC_SECONDS`, `UPLOAD_DELETE_AFTER_PROCESSING`, `CASESTRAINER_LOG_FULL_API_RESPONSES`) and in the worker (`src/rq_worker_pipeline.py`), enqueue paths, and related modules.
