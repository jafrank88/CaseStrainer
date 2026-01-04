#!/usr/bin/env python3
"""
Job Health Monitor for CaseStrainer RQ Workers

This script monitors Redis for stuck jobs and automatically cleans them up.
It runs as a separate process and checks for jobs that have been in "started"
state for too long without progress.

Features:
- Detects jobs stuck in "started" state
- Automatically cleans up jobs older than threshold
- Logs cleanup actions for debugging
- Prevents queue from being blocked by stuck jobs
"""

import os
import sys
import time
import logging
import redis
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class JobHealthMonitor:
    """Monitors and cleans up stuck RQ jobs."""

    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL", "redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0")
        self.redis_conn = redis.from_url(self.redis_url)
        self.stuck_threshold = 300  # 5 minutes in seconds
        self.check_interval = 30  # Check every 30 seconds

    def check_job_health(self):
        """Check for stuck jobs and clean them up."""
        try:
            # Get all job keys
            job_keys = self.redis_conn.keys("rq:job:*")

            stuck_jobs = []
            current_time = time.time()

            for job_key in job_keys:
                try:
                    # Get job data
                    job_data = self.redis_conn.hgetall(job_key)

                    if not job_data:
                        continue

                    # Check if job is in started status
                    status_bytes = job_data.get(b"status", b"")
                    if not status_bytes:
                        continue

                    status = status_bytes.decode("utf-8")

                    if status == "started":
                        # Check when job was started
                        started_at_bytes = job_data.get(b"started_at", b"")

                        if started_at_bytes:
                            try:
                                # Handle both string and float timestamps
                                started_at_str = started_at_bytes.decode("utf-8")
                                started_time = float(started_at_str)
                                time_in_started = current_time - started_time

                                if time_in_started > self.stuck_threshold:
                                    job_id = job_key.decode("utf-8").replace("rq:job:", "")
                                    stuck_jobs.append(
                                        {
                                            "job_id": job_id,
                                            "time_in_started": time_in_started,
                                            "started_at": datetime.fromtimestamp(started_time),
                                        }
                                    )
                            except (ValueError, UnicodeDecodeError) as e:
                                logger.debug(f"Invalid started_at timestamp for job {job_key}: {e}")
                                continue

                except Exception as e:
                    logger.error(f"Error checking job {job_key}: {e}")

            # Clean up stuck jobs
            if stuck_jobs:
                logger.warning(f"Found {len(stuck_jobs)} stuck jobs, cleaning up...")

                for job in stuck_jobs:
                    self.cleanup_stuck_job(job["job_id"])
                    logger.info(f"Cleaned up job {job['job_id']} (stuck for {job['time_in_started']:.1f}s)")
            else:
                logger.debug("No stuck jobs found")

        except Exception as e:
            logger.error(f"Error in job health check: {e}")

    def cleanup_stuck_job(self, job_id):
        """Clean up a stuck job from Redis."""
        try:
            # Keys to clean up
            keys_to_delete = [
                f"rq:job:{job_id}",
                f"rq:executions:{job_id}",
                f"verification:job:{job_id}",
                f"verification:status:{job_id}",
                f"progress:{job_id}",
            ]

            # Find execution keys
            execution_keys = self.redis_conn.keys(f"rq:execution:{job_id}:*")
            keys_to_delete.extend([k.decode("utf-8") for k in execution_keys])

            # Delete all keys
            deleted_count = 0
            for key in keys_to_delete:
                try:
                    if self.redis_conn.exists(key):
                        self.redis_conn.delete(key)
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting key {key}: {e}")

            logger.info(f"Cleaned up {deleted_count} keys for stuck job {job_id}")

        except Exception as e:
            logger.error(f"Error cleaning up job {job_id}: {e}")

    def run(self):
        """Run the health monitor loop."""
        logger.info("Starting Job Health Monitor...")
        logger.info(f"Stuck threshold: {self.stuck_threshold}s")
        logger.info(f"Check interval: {self.check_interval}s")

        while True:
            try:
                self.check_job_health()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Health monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in health monitor: {e}")
                time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = JobHealthMonitor()
    monitor.run()
