# RQ worker crash-loop troubleshooting

When `docker compose ps` shows workers as **Restarting (1)**, they are crash-looping. Use these steps to find the cause.

## 1. View worker logs (most important)

```powershell
# Last 150 lines including stderr
docker logs casestrainer-rqworker1-prod 2>&1 | Select-Object -Last 150
```

Or follow logs in real time:

```powershell
docker logs -f casestrainer-rqworker1-prod 2>&1
```

Look for a **Python traceback** (e.g. `ImportError`, `ModuleNotFoundError`, `AttributeError`) or Redis/connection errors.

## 2. Run worker startup inside the container

This isolates import vs. runtime errors:

```powershell
docker compose -f docker-compose.prod.yml run --rm --no-deps -e PYTHONPATH=/app backend python -c "
import sys
sys.path.insert(0, '/app')
try:
    from src.rq_worker import process_citation_task_direct, queue
    print('OK: Worker imports succeeded')
except Exception as e:
    import traceback
    print('FAIL:', e)
    traceback.print_exc()
"
```

(Use `backend` so the same image/volumes as workers are used; workers use the same build context.)

## 3. Common causes

| Symptom | Likely cause |
|--------|----------------|
| `ModuleNotFoundError` or `ImportError` | Missing dependency in image or wrong `PYTHONPATH` |
| `redis.exceptions.ConnectionError` | `REDIS_URL` wrong or Redis not reachable from worker (same network) |
| Exit code 1 right after "Redis ready" | Failing import in `src/rq_worker.py` (e.g. `src.rq_worker_pipeline`, `src.verification_manager`) |
| OOM / killed | Job or worker using too much memory; consider increasing `mem_limit` or reducing doc size |

## 4. After fixing

Restart workers so they pick up code or env changes:

```powershell
docker compose -f docker-compose.prod.yml restart rqworker1 rqworker2
```

Then confirm they stay up:

```powershell
docker compose -f docker-compose.prod.yml ps
```
