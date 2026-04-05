#!/usr/bin/env python3
"""Job Health Monitor - cleans up stuck RQ jobs periodically."""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

import redis
from rq import Queue, Worker
from rq.job import Job
from rq.registry import StartedJobRegistry

from src.config import REDIS_URL, DATA_RETENTION_ASYNC_SECONDS
STUCK_THRESHOLD = int(os.environ.get("JOB_STUCK_THRESHOLD_SEC", "600"))
MONITOR_INTERVAL = int(os.environ.get("MONITOR_INTERVAL_SEC", "60"))
QUEUE_NAME = "casestrainer"

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - job-health-monitor - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "job-health-monitor.log")),
    ],
)
logger = logging.getLogger(__name__)

_shutdown = False


def _task_has_recent_progress(conn, job_id: str) -> bool:
    """Return True if task progress/status appears to have been updated recently enough to treat the job as active."""
    now_ts = time.time()
    candidates = [
        f"verification_status:{job_id}",
        f"task_status:{job_id}",
        f"task_progress:{job_id}",
        f"task_result:{job_id}",
    ]
    for key in candidates:
        try:
            if not conn.exists(key):
                continue
            ttl = conn.ttl(key)
            if ttl and ttl > max(30, MONITOR_INTERVAL):
                return True
            raw = conn.get(key)
            if not raw:
                continue
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            data = json.loads(raw)
            if not isinstance(data, dict):
                continue
            for field in ("updated_at", "last_updated", "timestamp"):
                val = data.get(field)
                if isinstance(val, (int, float)) and (now_ts - float(val)) <= max(90, MONITOR_INTERVAL * 2):
                    return True
        except Exception:
            continue
    return False

def _handle_signal(signum, _frame):
    global _shutdown
    logger.info("Received signal %s - shutting down", signum)
    _shutdown = True

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


def cleanup_stuck_jobs(conn):
    cleaned = 0
    try:
        registry = StartedJobRegistry(QUEUE_NAME, connection=conn)
        for job_id in registry.get_job_ids():
            try:
                job = Job.fetch(job_id, connection=conn)
            except Exception:
                try:
                    registry.remove(job_id)
                except Exception:
                    pass
                continue
            started_at = job.started_at
            if started_at is None:
                continue
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            if elapsed > STUCK_THRESHOLD:
                if _task_has_recent_progress(conn, job_id):
                    logger.info(
                        "Job %s exceeded threshold (%.0fs) but has recent progress; leaving it active",
                        job_id, elapsed,
                    )
                    continue
                logger.warning(
                    "Job %s stuck %.0fs (threshold %ds) func=%s - cancelling",
                    job_id, elapsed, STUCK_THRESHOLD, job.func_name,
                )
                try:
                    job.cancel()
                    registry.remove(job_id)
                    cleaned += 1
                    result_key = f"task_result:{job_id}"
                    if not conn.exists(result_key):
                        conn.setex(result_key, DATA_RETENTION_ASYNC_SECONDS, json.dumps({
                            "success": False,
                            "error": f"Job timed out after {int(elapsed)}s",
                            "citations": [], "clusters": [],
                        }))
                except Exception as e:
                    logger.error("Failed to clean job %s: %s", job_id, e)
    except Exception as e:
        logger.error("Error scanning started registry: %s", e)
    return cleaned


def main():
    logger.info(
        "Starting: threshold=%ds, interval=%ds, queue=%s",
        STUCK_THRESHOLD, MONITOR_INTERVAL, QUEUE_NAME,
    )
    conn = redis.from_url(REDIS_URL)
    conn.ping()
    logger.info("Redis connected")

    while not _shutdown:
        try:
            cleaned = cleanup_stuck_jobs(conn)
            q = Queue(QUEUE_NAME, connection=conn)
            workers = Worker.all(connection=conn)
            active = [w for w in workers if w.state in ("busy", "idle")]
            logger.info(
                "Sweep: cleaned=%d, pending=%d, workers=%d",
                cleaned, q.count, len(active),
            )
        except redis.exceptions.ConnectionError:
            logger.error("Redis connection lost - reconnecting")
            try:
                conn = redis.from_url(REDIS_URL)
                conn.ping()
            except Exception:
                pass
        except Exception as e:
            logger.error("Monitor error: %s", e)

        for _ in range(MONITOR_INTERVAL):
            if _shutdown:
                break
            time.sleep(1)

    logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
