#!/usr/bin/env python
"""Diagnose RQ worker and queue status"""
from rq import Queue, Worker
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
from redis import Redis
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)

print("="*60)
print("RQ DIAGNOSTICS")
print("="*60)

# Queue status
q = Queue('casestrainer', connection=redis_conn)
print(f"\nQueue: casestrainer")
print(f"  Jobs in queue: {len(q)}")
print(f"  Queue is empty: {q.is_empty()}")

# Registries
started_reg = StartedJobRegistry('casestrainer', connection=redis_conn)
finished_reg = FinishedJobRegistry('casestrainer', connection=redis_conn)
failed_reg = FailedJobRegistry('casestrainer', connection=redis_conn)

print(f"\nStarted jobs: {len(started_reg)}")
for job_id in list(started_reg.get_job_ids())[:5]:
    try:
        job = q.fetch_job(job_id)
        if job:
            print(f"  - {job_id[:20]}... status={job.get_status()}, started={job.started_at}")
    except Exception as e:
        print(f"  - {job_id[:20]}... ERROR: {e}")

print(f"\nFinished jobs (last 5): {len(finished_reg)}")
for job_id in list(finished_reg.get_job_ids())[:5]:
    print(f"  - {job_id[:20]}...")

print(f"\nFailed jobs: {len(failed_reg)}")
for job_id in list(failed_reg.get_job_ids())[:5]:
    try:
        job = q.fetch_job(job_id)
        if job:
            print(f"  - {job_id[:20]}... ERROR: {job.exc_info}")
    except Exception as e:
        print(f"  - {job_id[:20]}... ERROR: {e}")

# Workers
print(f"\nWorkers:")
workers = Worker.all(connection=redis_conn)
print(f"  Total workers: {len(workers)}")
for worker in workers[:3]:
    print(f"  - {worker.name}")
    print(f"    State: {worker.get_state()}")
    current_job = worker.get_current_job()
    if current_job:
        print(f"    Current job: {current_job.id}")
        print(f"    Job status: {current_job.get_status()}")

print("\n" + "="*60)
