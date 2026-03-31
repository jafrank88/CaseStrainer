# Rollback runbook

## Trigger conditions (examples)

Rollback or freeze traffic if **any** of the following persist after a deploy:

- Health endpoint unhealthy for more than **5 minutes** (`/casestrainer/api/health`).
- **Sustained** Redis queue growth (e.g. `LLEN rq:queue:casestrainer` increasing for **30+ minutes**) with workers running.
- **Repeated OOM** or crash loops on `backend` or majority of `rqworker` containers.
- **Spike** in 5xx rate or complete loss of successful analyzes vs baseline.
- **Data integrity**: verified citations systematically wrong on gold documents (stop traffic, investigate).

## Rollback command (Docker Compose production)

1. Note current image or git SHA (for postmortem).
2. Check out or pull the **previous stable tag/commit**.
3. Rebuild/restart with the same env file (no secret changes):

```bash
docker compose -f docker-compose.prod.yml pull   # if using registry images
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

4. Verify: `curl -sf http://localhost:5000/casestrainer/api/health` (adjust host/port).
5. Verify queue drains: `docker exec <redis-container> redis-cli -a "$REDIS_PASSWORD" LLEN rq:queue:casestrainer`

## Previous stable artifact

- **Image tag / digest:** _record at release time_
- **Git tag / SHA:** _record at release time_

## On-call

- **Primary:** _name / contact_
- **Secondary:** _name / contact_

## Tested?

- [x] Rollback steps documented above; **dry-run on staging:** _operator records date / name here before public launch_
