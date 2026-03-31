# Post-release monitoring (first 24–48 hours)

Execute these checks after the site is public or on a production-like environment. Log observations in `docs/go-live-evidence/MONITORING_LOG.md` (create if missing).

## 1) Strict-gate and `possible_match`

- Watch logs or metrics for **strict-gate reject** volume vs baseline.
- Track **`possible_match`** rate and top rejection reasons (search logs for `GATE-REJECT`, `possible_match`).

## 2) Verification fallbacks

- Sample logs for **fallback success** by source (CourtListener, search, web) — ensure no unexpected spike in failures or wrong-case pairings.

## 3) Workers and queue

- **Queue depth:** `LLEN rq:queue:casestrainer` (or your queue name) should stay near usual range; alert on sustained growth.
- **Restarts:** `docker compose -f docker-compose.prod.yml ps` and `docker inspect` / orchestrator events — no **OOM/restart loops** under normal traffic.
- **Worker OOM:** watch container memory vs limits during peak; scale down traffic or workers if unstable.

## 4) API

- Error rate and latency (p50/p95) vs pre-release baseline.
- **429** rate (rate limiting) — distinguish from server errors.

## 5) Triage

- File issues for **false positives/negatives** in verification or clustering with document ids and sample cites.

## Quick commands (reference)

```bash
docker compose -f docker-compose.prod.yml ps
curl -s http://localhost:5000/casestrainer/api/health
docker logs --tail 200 casestrainer-backend-prod
docker logs --tail 200 casestrainer-rqworker1-prod
# Redis queue (use your password from env; do not commit it):
docker exec casestrainer-redis-prod redis-cli -a "${REDIS_PASSWORD}" LLEN rq:queue:casestrainer
```
