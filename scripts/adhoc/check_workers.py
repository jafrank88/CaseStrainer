#!/usr/bin/env python3
"""Check RQ worker status"""
import redis
from rq import Queue, Worker
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

# Connect to Redis
r = redis.Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0)

# Get queue
q = Queue('casestrainer', connection=r)

print("="*60)
print("RQ WORKER STATUS")
print("="*60)

# Queue stats
print(f"\n📋 Queue: 'casestrainer'")
print(f"  Queued jobs: {len(q)}")
print(f"  Started jobs: {len(q.started_job_registry)}")
print(f"  Finished jobs: {len(q.finished_job_registry)}")
print(f"  Failed jobs: {len(q.failed_job_registry)}")

# Workers
workers = Worker.all(connection=r)
print(f"\n👷 Active Workers: {len(workers)}")
for worker in workers:
    state = worker.get_state()
    current_job = worker.get_current_job()
    job_info = f" - Processing: {current_job.id if current_job else 'idle'}"
    print(f"  • {worker.name} ({state}){job_info}")

# Started jobs details
if len(q.started_job_registry) > 0:
    print(f"\n🔄 Currently Processing:")
    started = StartedJobRegistry('casestrainer', connection=r)
    for job_id in started.get_job_ids():
        job = q.fetch_job(job_id)
        if job:
            print(f"  • {job_id}: {job.func_name}")

# Recent finished jobs
if len(q.finished_job_registry) > 0:
    print(f"\n✅ Recently Finished (last 10):")
    finished = FinishedJobRegistry('casestrainer', connection=r)
    for job_id in list(finished.get_job_ids())[:10]:
        job = q.fetch_job(job_id)
        if job:
            status = "✅" if job.is_finished else "❌"
            print(f"  {status} {job_id}")

# Failed jobs
if len(q.failed_job_registry) > 0:
    print(f"\n❌ Failed Jobs:")
    failed = FailedJobRegistry('casestrainer', connection=r)
    for job_id in failed.get_job_ids():
        job = q.fetch_job(job_id)
        if job:
            print(f"  • {job_id}: {job.exc_info}")

print("\n" + "="*60)
