# RQ worker scaling (memory)

How many workers you can run depends on host RAM and the limits set in `docker-compose.prod.yml`.

## Current memory settings (32 GB machine)

| Service | Limit | Reservation |
|--------|--------|-------------|
| **backend** | 4 GB | 2 GB |
| **rqworker1–rqworker6** | 4 GB each | 1 GB each |
| **job-health-monitor** | 512 MB | 256 MB |
| **redis** | (default) | — |
| **nginx** | (default) | — |
| **frontend-prod** | (default) | — |

Each **worker** is configured with:

- `mem_limit: 4g` (hard cap per container)
- `mem_reservation: 1g` (reserved for the container)
- `RQ_MAX_MEMORY_MB=2048` (RQ’s internal “restart worker if a job uses more than 2 GB” hint)

So **one worker** is **~4 GB** for capacity planning. **Six workers** = 24 GB; with ~8 GB for backend and other services, total fits **32 GB**.

## How many workers fit

Use:

```text
  max_workers ≈ (host_RAM_GB - 8) / 4
```

Rough “other services” total (backend + redis + nginx + frontend + job-health-monitor): **~6–8 GB**.  
(~8 GB for other services + buffer.)

| Host RAM | Max workers (4 GB each) |
|----------|--------------------------|
| 16 GB    | 2                        |
| 24 GB    | 4                        |
| 32 GB    | 6                        |
| 48 GB    | 10                       |


## Adding more workers

Compose already defines **rqworker1–rqworker6** (4 GB each for 32 GB host). To add more or run fewer:

1. Scale up: `docker compose -f docker-compose.prod.yml up -d rqworker3 rqworker4 rqworker5 rqworker6` (if not already running).
2. Scale down: stop unneeded workers, e.g. `docker compose -f docker-compose.prod.yml stop rqworker4 rqworker5 rqworker6`.
3. To add rqworker7+, copy an existing worker block in `docker-compose.prod.yml`, set `container_name`, `WORKER_ID`, and ensure host RAM ≥ 8 + (4 × number_of_workers).

## 4 GB per worker (this machine)

If you use **4 GB per worker** (`mem_limit: 4g`, `mem_reservation: 1g`, `deploy.resources.limits.memory: 4G`, and `RQ_MAX_MEMORY_MB=2048`):

- **Other services** (backend, redis, nginx, frontend, job-health-monitor + buffer): **~8 GB**.
- **Formula:** `max_workers_4g ≈ (host_RAM_GB - 8) / 4`.

| Host RAM | Max workers (4 GB each) |
|----------|--------------------------|
| 16 GB    | 2                        |
| 24 GB    | 4                        |
| 32 GB    | 6                        |
| 48 GB    | 10                       |

**This machine (32 GB):** with 4 GB per worker you can run **6 workers** (32 − 8 ≈ 24 GB for workers, 24 ÷ 4 = 6).

## Reducing memory per worker

If you need more workers on the same host, lower per-worker limits in `docker-compose.prod.yml`, for example:

- `mem_limit: 4g` / `mem_reservation: 1g` and `deploy.resources.limits.memory: 4G`  
Then: `max_workers ≈ (host_RAM_GB - 8) / 4`.  
Monitor for OOM; citation/verification jobs can be memory-heavy.

## Running sync as async (SYNC_REQUESTS_AS_ASYNC)

When **`SYNC_REQUESTS_AS_ASYNC=true`** (env or config), any request with `force_mode=sync` is run as async: the job is enqueued and the API returns `task_id` + `status=processing` immediately. The client can poll `task_status/<task_id>` until completion. This:

- Avoids long-blocking HTTP connections and frees backend memory.
- Lets you run more workers (no in-process sync work on the backend).
- Requires the client to poll for results (same as async).

Set in `.env` or `config.env`:

```bash
SYNC_REQUESTS_AS_ASYNC=true
```

Then restart the backend. Frontend or scripts that send `force_mode=sync` should poll `task_status` when they receive `status=processing` and a `task_id`.
