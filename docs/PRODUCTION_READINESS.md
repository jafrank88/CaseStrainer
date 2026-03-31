# Production Readiness Review

This document summarizes findings from a codebase review for production deployment. Items are grouped by priority: **Critical**, **High**, **Medium**, and **Low**.

---

## Critical

### 1. Secrets and credentials

- **Hardcoded API keys and Redis password**
  - `docker-compose.prod.yml` and several backend files use a fallback Redis URL containing the password `***REDACTED_REDIS_PASSWORD***` and the CourtListener API key `***REDACTED_COURTLISTENER_KEY***`.
  - **Action:** Never commit real secrets. Use env vars only (e.g. `REDIS_URL`, `COURTLISTENER_API_KEY`) and ensure `config.env` and `.env` are in `.gitignore` and never committed. For Docker, pass secrets via env files or a secrets manager at deploy time.
- **Frontend CourtListener API key**
  - The Vue build bakes `VITE_COURTLISTENER_API_KEY` into the client bundle (visible to anyone). `Dockerfile.prod` now uses an `ARG` so the value can be passed at build time (`docker build --build-arg VITE_COURTLISTENER_API_KEY=...`) instead of hardcoding; do not commit the key in the Dockerfile or compose files.
  - **Action:** If CourtListener allows client-side keys, document that. Otherwise, proxy CourtListener requests through the backend and keep the key only in server env.
- **`config.env`**
  - Contains secrets in some setups. `config.env` has been added to `.gitignore` so it is not committed; use `.env` or env vars for local dev and inject secrets at deploy time.

### 2. Default Flask secret key

- **Location:** `src/config.py` – `SECRET_KEY = get_config_value("SECRET_KEY", "devkey")`.
- **Risk:** In production, a weak or default secret can compromise sessions and signed data.
- **Action:** Require a strong `SECRET_KEY` in production (e.g. fail startup or refuse to run with "devkey" when `ENVIRONMENT=production` or `FLASK_ENV=production`).

---

## High

### 3. Rate limiting on main API

- **Finding:** `src/rate_limiter.py` exists and is imported in `app_final_vue.py`, but the `/analyze` POST endpoint (and other vue_api routes) do **not** use `@rate_limit` or `validate_input`. The heavy `/analyze` path is unprotected.
- **Action:** Apply rate limiting to the analyze endpoint (and optionally to task_status and progress). Example: register the vue_api blueprint with a before_request that runs the rate limiter, or wrap the analyze view with `@rate_limit(max_calls=..., window=...)` (e.g. per IP or per user). Use config (env) for limits.

### 4. CORS and response headers

- **Finding:** Some route modules set `Access-Control-Allow-Origin: *` on responses (e.g. `src/api/routes/metrics.py`, `src/api/routes/progress.py`, `src/api/routes/verification.py`). The main app uses `_configure_cors` with `CORS_ORIGINS` from env, which is better.
- **Risk:** `*` allows any origin; if combined with credentials or sensitive data, that can be unsafe.
- **Action:** Prefer a single CORS configuration (e.g. Flask-CORS on the app) and avoid ad-hoc `*` in route-level headers unless intentionally public read-only endpoints. For production, set `CORS_ORIGINS` to the exact frontend origin(s).

### 5. Logging and debugging in production

- **Finding:** Many `console.log`/`console.debug`/`print` and some `logger.info` calls with verbose or sensitive data (e.g. request IDs, file names, URLs) in:
  - Backend: `src/vue_api_endpoints_updated.py`, `src/rq_worker_pipeline.py`, `src/unified_input_processor.py`, etc.
  - Frontend: `HomeView.vue`, `CitationResults.vue` (composables), `api.js`, `progressStore.js`, etc.
- **Action:** Use a log level (e.g. `DEBUG`) and environment (e.g. `VITE_APP_ENV`, `FLASK_ENV`) so that verbose/debug logs are disabled or stripped in production builds. Avoid logging full request bodies, tokens, or API keys. Consider a small logging utility that no-ops in production for frontend.

### 6. Error handling and information leakage

- **Finding:** Health and some error paths include `traceback.format_exc()` in JSON responses. That can expose stack traces and paths to clients.
- **Action:** In production, return generic error messages to the client and log full tracebacks server-side only. Use `FLASK_DEBUG=0` and a production error handler that does not attach tracebacks to responses.

---

## Medium

### 7. Redis URL fallback

- **Finding:** Multiple files use a hardcoded fallback when `REDIS_URL` is missing, e.g. `redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0` in `src/rq_worker.py`, `src/rq_worker_pipeline.py`, `src/vue_api_endpoints_updated.py`, `src/verification_manager.py`, `src/job_health_monitor.py`, `src/unified_input_processor.py`.
- **Action:** In production, require `REDIS_URL` (fail fast if unset). Use a safe dev-only fallback (e.g. `redis://localhost:6379/0`) only when `ENVIRONMENT=development` or similar.

### 8. File upload validation

- **Finding:** Backend uses `MAX_CONTENT_LENGTH` (50MB in config) and allowed extensions. Frontend checks file size (e.g. 50MB in `HomeView.vue`). No virus or content-type deep validation was seen.
- **Action:** Keep and document max size and allowed types. Consider scanning uploads in production (e.g. ClamAV or cloud scanning) and validating content type (e.g. magic bytes) in addition to extension.

### 9. Health check and dependencies

- **Finding:** Health endpoint checks DB, upload directory, and citation processor. It does not explicitly check Redis or the RQ worker queue.
- **Action:** Add optional Redis connectivity check (and optionally queue length) to health so orchestration can restart workers or scale when Redis is down or backlogged. Document health contract for load balancers and k8s.

### 10. Timeouts and long-running requests

- **Finding:** Analyze uses long timeouts (e.g. 600s for file, 300s for URL). Frontend polling and SSE streams have their own timeouts.
- **Action:** Document timeout strategy (client, reverse proxy, app server, RQ job timeout). Ensure proxy (e.g. nginx) timeouts are ≥ backend timeouts for analyze and SSE. Consider a “job status” UX when approaching timeout.

---

## Low

### 11. Deprecated and duplicate code

- **Finding:** `EnhancedValidator.vue` is deprecated but still in tree. `vue_api_endpoints.py` (old) coexists with `vue_api_endpoints_updated.py`. Some ad-hoc scripts in `scripts/adhoc/` may still reference old paths.
- **Action:** Remove or clearly mark deprecated UI and API files; add a single “canonical” entry for the Vue API (already documented in `docs/CODE_STRUCTURE_IMPROVEMENTS.md` and `docs/PIPELINE_ENTRY_POINTS.md`). Clean or archive ad-hoc scripts that are obsolete.

### 12. Tests and CI

- **Finding:** `.gitignore` excludes `tests/` then re-includes specific test files. CI runs health check and security scan.
- **Action:** Confirm CI runs the full test suite (pytest) and that critical paths (analyze, task_status, verification) are covered. Add a simple smoke test for analyze (e.g. minimal text input) if missing.

### 13. Frontend env and build

- **Finding:** Production frontend build bakes in `VITE_*` at build time. Changing API base URL or feature flags requires a new build.
- **Action:** Document required `VITE_*` vars for production (see `.env.example`). For multi-environment deploys, use build-time ARGs in Docker and pass env from CI/CD.

### 14. Metrics and observability

- **Finding:** Metrics routes exist (`/metrics/summary`, `/metrics/series`, dashboard). Sentry is optional via `SENTRY_DSN`.
- **Action:** In production, enable Sentry (or similar) and optionally restrict `/metrics` to internal or admin IPs. Consider alerting on error rate and queue depth.

---

## Checklist summary

| Area                | Action |
|---------------------|--------|
| Secrets             | No hardcoded keys/passwords; use env only; add `config.env` to `.gitignore`. |
| SECRET_KEY          | Require strong value in production. |
| Rate limiting       | Apply to `/analyze` (and optionally task_status). |
| CORS                | Use explicit origins from env; avoid `*` for sensitive routes. |
| Logging             | Reduce verbosity and PII in production; no tracebacks in client responses. |
| Redis               | Require `REDIS_URL` in production; no default prod password in code. |
| Health              | Optional Redis/queue check; document for operators. |
| Timeouts            | Document and align proxy/app/job timeouts. |
| Deprecated code     | Remove or clearly mark; keep one canonical API entry. |
| Tests/CI            | Run full suite; add smoke test for analyze if needed. |
| Observability       | Enable error tracking; consider restricting metrics. |
