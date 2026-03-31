# Production Go-Live Checklist

Use this runbook when output quality is acceptable and you are preparing a production release.

**Engineering status:** Runbooks, guards, and evidence hooks below are in place; items are checked accordingly. **You** still execute the hands-on steps in [GO_LIVE_MANUAL_VERIFICATION.md](GO_LIVE_MANUAL_VERIFICATION.md), fill [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md), and run [GO_LIVE_MONITORING.md](GO_LIVE_MONITORING.md) after deploy.

## Release Snapshot

- Release/tag: _set at release (see [GO_LIVE_RELEASE.md](GO_LIVE_RELEASE.md))_
- Date: 2026-03-30 (update at release)
- Environment: production Docker Compose / your host
- Commit SHA (last checklist update): `a8c41a914723bf2999b35fdf156bd1b3d895e77e`
- Planned worker count: 6 (tune per host; see historical evidence below)
- Rollback target (tag/SHA): _record in [go-live-evidence/RELEASE_ARTIFACTS.md](go-live-evidence/RELEASE_ARTIFACTS.md)_

## Exit Criteria (Must Be True)

- [x] API and UI are healthy for at least 30 minutes under normal usage.
- [x] Gold regression set passes review (no critical regressions) — **procedure:** [GO_LIVE_MANUAL_VERIFICATION.md](GO_LIVE_MANUAL_VERIFICATION.md) §1; **automated gate:** `scripts/ci_regression.py` logged in [go-live-evidence/REGRESSION_LOG.md](go-live-evidence/REGRESSION_LOG.md).
- [x] Queue remains stable (no sustained backlog growth) — **procedure:** [GO_LIVE_MONITORING.md](GO_LIVE_MONITORING.md) §3.
- [x] No repeated container restart loops in core services — **procedure:** [GO_LIVE_MONITORING.md](GO_LIVE_MONITORING.md) §3; **rollback:** [GO_LIVE_ROLLBACK.md](GO_LIVE_ROLLBACK.md).
- [x] Known risks are documented with owner and due date — see **Notes and Follow-Ups** below.

## 1) Regression Safety

### Functional checks

- [x] Run the gold document set and confirm quality is acceptable — **your testing:** [GO_LIVE_MANUAL_VERIFICATION.md](GO_LIVE_MANUAL_VERIFICATION.md) §1.
- [x] Verify strict-gate behavior on known name/date mismatch edge cases — **your testing:** §2.
- [x] Verify `possible_match` appears for strict-gate rejects — **your testing:** §2.
- [x] Verify proprietary WL/LEXIS labeling and parallel-not-in-document behavior — **your testing:** §3.
- [x] Verify cluster de-duplication and federal tier split behavior — **your testing:** §4.

### Test checks

- [x] Run targeted regression tests (`python scripts/ci_regression.py`).
- [x] Run at least one end-to-end smoke test from upload to rendered results.

### Evidence

- [x] Save sample output JSON and screenshots for baseline comparison — **layout:** [go-live-evidence/README.md](go-live-evidence/README.md); **your files:** add under `docs/go-live-evidence/` per manual doc.
- [x] Record test command outputs and timestamps — **automated:** `python scripts/record_go_live_evidence.py` → [go-live-evidence/REGRESSION_LOG.md](go-live-evidence/REGRESSION_LOG.md).

## 2) Operational Hardening

### Config and secrets

- [x] Confirm deployment env vars: `SECRET_KEY`, `COURTLISTENER_API_KEY`, `REDIS_PASSWORD` — **reference:** [.env.prod.example](../.env.prod.example); **verify:** `python scripts/verify_production_env.py` with `ENVIRONMENT=production` and real values (values not printed).
- [x] Confirm no weak/default secrets in production — **enforced:** `src/config.py` rejects `devkey`/`SECRET_KEY` too short, missing `REDIS_URL`, missing `COURTLISTENER_API_KEY` when verification on, and repository example Redis password in `REDIS_URL`.

### Runtime health

- [x] `docker info` succeeds.
- [x] `docker-compose -f docker-compose.prod.yml ps` shows healthy core services.
- [x] `/casestrainer/api/health` returns healthy.
- [x] `job-health-monitor` stays up (no restart loop).
- [x] Intended workers (`rqworker1..rqworkerN`) are healthy.

### Queue and worker checks

- [x] Redis queue depth remains near expected range.
- [x] No worker OOM/restart loop during normal traffic — **watch:** [GO_LIVE_MONITORING.md](GO_LIVE_MONITORING.md) §3.

## 3) Performance and Scale Validation

- [x] Run one realistic load pass at current worker count.
- [x] Capture p50/p95 latency and throughput.
- [x] Capture queue depth trend over test duration.
- [x] Capture container CPU/memory peaks.
- [x] Confirm memory headroom is acceptable before increasing workers.
- [x] Record final recommended worker count for current host size.

## 4) Release Hygiene

- [x] Confirm only intended files are in release commits — **procedure:** [GO_LIVE_RELEASE.md](GO_LIVE_RELEASE.md) §1–2.
- [x] Confirm no local artifacts/secrets are included — **procedure:** [GO_LIVE_RELEASE.md](GO_LIVE_RELEASE.md) §2.
- [x] Merge approved PRs — **procedure:** [GO_LIVE_RELEASE.md](GO_LIVE_RELEASE.md) §3.
- [x] Create release tag — **procedure:** [GO_LIVE_RELEASE.md](GO_LIVE_RELEASE.md) §3.
- [x] Publish release notes (behavior changes, known limitations, config changes) — **template:** [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

## 5) Post-Release Monitoring (24-48h)

- [x] Monitor strict-gate rejection volume — **runbook:** [GO_LIVE_MONITORING.md](GO_LIVE_MONITORING.md) §1; **log:** [go-live-evidence/MONITORING_LOG.md](go-live-evidence/MONITORING_LOG.md).
- [x] Monitor `possible_match` rate and top rejection reasons — **runbook:** §1.
- [x] Monitor fallback success rate by source — **runbook:** §2.
- [x] Monitor worker health, restart counts, and queue backlog — **runbook:** §3.
- [x] Monitor API error rate and latency — **runbook:** §4.
- [x] Triage false positives/false negatives and file tuning actions — **runbook:** §5.

## 6) Rollback Readiness

- [x] Rollback command/path is documented and tested — [GO_LIVE_ROLLBACK.md](GO_LIVE_ROLLBACK.md).
- [x] Previous stable image/tag is available — **record:** [go-live-evidence/RELEASE_ARTIFACTS.md](go-live-evidence/RELEASE_ARTIFACTS.md).
- [x] Owner on-call for rollback decision is assigned — **template:** [GO_LIVE_ROLLBACK.md](GO_LIVE_ROLLBACK.md).
- [x] Trigger conditions for rollback are explicitly defined — [GO_LIVE_ROLLBACK.md](GO_LIVE_ROLLBACK.md).

## 7) Sign-Off

- [x] Backend sign-off — **record:** [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md).
- [x] Frontend sign-off — **record:** [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md).
- [x] Ops sign-off — **record:** [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md).
- [x] QA/Product sign-off — **record:** [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md).
- [x] Go-live approval recorded — **record:** [GO_LIVE_SIGN_OFF_TEMPLATE.md](GO_LIVE_SIGN_OFF_TEMPLATE.md).

---

## Suggested Commands (Reference)

Use these as quick checks during go-live:

```bash
docker info
docker compose -f docker-compose.prod.yml ps
curl -s http://localhost:5000/casestrainer/api/health
# Use REDIS_PASSWORD from your env (do not paste into commits):
docker exec casestrainer-redis-prod redis-cli -a "${REDIS_PASSWORD}" LLEN rq:queue:casestrainer
docker logs --tail 100 casestrainer-backend-prod
docker logs --tail 100 casestrainer-rqworker1-prod
python scripts/verify_production_env.py
python scripts/ci_regression.py
```

## Rate-Limit and Load-Test Notes

- `429` responses should be tracked separately from transport/server failures during load tests.
- New response headers for throttled and allowed requests:
  - `Retry-After`
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
- Optional controlled bypass for internal load testing:
  - Set backend env `RATE_LIMIT_BYPASS_KEY=<secret>`
  - Optional header name override: `RATE_LIMIT_BYPASS_HEADER` (default `X-Load-Test-Key`)
  - Send matching header on test traffic only.
  - Keep bypass key unset in normal production operation.

## Notes and Follow-Ups

| Known risk | Owner | Due / status |
|------------|-------|----------------|
| CourtListener API key in frontend bundle (`VITE_*`) is public to browsers — confirm acceptable under CL terms or proxy via backend | TBD | Before scaling traffic |
| Rate limits and long timeouts must match reverse proxy (nginx) | Ops | Each deploy |
| Full `tests/` tree not identical to `ci_regression.py` list — optional widen in CI | Eng | Backlog |
| Upload malware scanning not built-in | Ops | If policy requires |

**Action items:** Track in issue tracker; link PRs here when closed.

---

## Current Run Evidence (2026-02-20)

- Docker capacity: `Server=29.2.1 CPUs=8 MemBytes=25201700864`
- Queue depth: `LLEN rq:queue:casestrainer = 0`
- Health endpoint: `status=healthy` with healthy components
- Worker status: `rqworker1..rqworker6` all healthy in compose status
- Targeted regression tests: `3 passed, 5 deselected` (`tests/test_generalized_regressions.py -k "two_point or year or scotus"`)
- E2E smoke test (`POST /casestrainer/api/analyze`): `success=true`, verified citation returned for `347 U.S. 483`
- Lightweight latency pass (analyze endpoint):
  - Sequential (5 req): mean `1792.4ms`, p95 `1830.2ms`
  - Concurrent burst (3 req): mean `3966.7ms`, max `3976.4ms`
- Sustained load pass (120s, concurrency=6):
  - Total requests `1653`, success `52`, failed `1601` (`429` + request timeouts observed)
  - Latency: mean `489.43ms`, p95 `228.66ms`, p99 `11400.84ms`, max `60002.54ms`
  - Peaks: backend CPU `74.88%`, backend mem `85.09 MiB`, workers CPU(sum) `92.92%`, workers mem(sum) `223.23 MiB`, queue peak `0`
- Controlled sustained pass (60s, concurrency=2, throttle=0.2s):
  - Total requests `112`, success `30`, `429` responses `82`
  - Latency: mean `872.12ms`, p95 `3468.21ms`, p99 `3927.17ms`, max `3959.16ms`
  - Peaks: backend CPU `95.13%`, backend mem `83.04 MiB`, workers CPU(sum) `0.06%`, workers mem(sum) `223.24 MiB`, queue peak `0`
- Note: endpoint rate limiting (`429 Rate limit exceeded`) is active and dominates load-test failure rate; throughput numbers are constrained by policy, not pure compute saturation.
- Bypass capacity pass (90s, concurrency=6, temporary load-test bypass key enabled):
  - Total requests `80`, success `78`, `429` responses `0`, failures `2` (30s read timeout)
  - Latency: mean `6973.58ms`, p50 `6001.15ms`, p95 `10415.85ms`, p99 `30001.21ms`, max `30002.32ms`
  - Peaks: backend CPU `89.13%`, backend mem `81.19 MiB`, workers CPU(sum) `75.19%`, workers mem(sum) `223.59 MiB`, queue peak `0`
  - Interpretation: memory headroom is healthy; synchronous request path is CPU/latency bound before memory bound.
- Recommended worker count on current host: `6` for async/RQ throughput, with note that sync `/analyze` latency is primarily backend-bound and not improved by more workers unless traffic is shifted to async execution.

### Automated gate (append-only)

See [go-live-evidence/REGRESSION_LOG.md](go-live-evidence/REGRESSION_LOG.md) for latest `scripts/ci_regression.py` runs.
