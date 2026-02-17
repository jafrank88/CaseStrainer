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

from src.config import REDIS_URL
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
                        conn.setex(result_key, 86400, json.dumps({
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
