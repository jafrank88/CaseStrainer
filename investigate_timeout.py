"""
Investigate why processing is timing out after 5 minutes
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

import asyncio
import time
from datetime import datetime

# Check what's happening with timeouts
print("=" * 80)
print("INVESTIGATING PROCESSING TIMEOUT")
print("=" * 80)

# 1. Check if Docker is running
print("\n1. Checking Docker status...")
try:
    import docker
    client = docker.from_env()
    containers = client.containers.list(all=True)
    
    casestrainer_containers = [c for c in containers if 'casestrainer' in c.name.lower()]
    print(f"Found {len(casestrainer_containers)} CaseStrainer containers:")
    
    for container in casestrainer_containers:
        print(f"  - {container.name}: {container.status}")
        if container.status == 'running':
            print(f"    Started: {container.attrs['State']['StartedAt']}")
except Exception as e:
    print(f"Docker error: {e}")

# 2. Check Redis connection
print("\n2. Checking Redis connection...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("✅ Redis is running")
    
    # Check for stuck jobs
    stuck_jobs = r.lrange("celery", 0, -1)
    print(f"Jobs in queue: {len(stuck_jobs)}")
    
    # Check active workers
    workers = r.smembers("celery:active")
    print(f"Active workers: {len(workers)}")
    
except Exception as e:
    print(f"❌ Redis error: {e}")

# 3. Check backend service
print("\n3. Checking backend service...")
import requests
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"Backend health: {response.status_code}")
except requests.exceptions.Timeout:
    print("❌ Backend timed out")
except requests.exceptions.ConnectionError:
    print("❌ Backend not responding")
except Exception as e:
    print(f"❌ Backend error: {e}")

# 4. Check recent logs for timeout issues
print("\n4. Checking for timeout issues in logs...")
import os
import glob

log_files = [
    "D:/dev/casestrainer/logs/app.log",
    "D:/dev/casestrainer/logs/celery.log",
    "D:/dev/casestrainer/logs/nginx/access.log",
    "D:/dev/casestrainer/logs/docker_daemon_monitor.log"
]

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\nChecking {os.path.basename(log_file)}...")
        try:
            # Read last 50 lines
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-50:]
                
            # Look for timeout or error messages
            for line in lines:
                if any(keyword in line.lower() for keyword in ['timeout', 'timed out', 'error', 'exception', 'failed']):
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"  Error reading log: {e}")

# 5. Check system resources
print("\n5. Checking system resources...")
import psutil

# CPU usage
cpu_percent = psutil.cpu_percent(interval=1)
print(f"CPU usage: {cpu_percent}%")

# Memory usage
memory = psutil.virtual_memory()
print(f"Memory usage: {memory.percent}% ({memory.used/1024/1024/1024:.1f}GB used)")

# Disk usage
disk = psutil.disk_usage('/')
print(f"Disk usage: {disk.percent}% ({disk.used/1024/1024/1024:.1f}GB used)")

print("\n" + "=" * 80)
print("COMMON TIMEOUT CAUSES:")
print("-" * 40)
print("1. Redis not running or connection lost")
print("2. Celery workers stuck or crashed")
print("3. Docker container out of memory")
print("4. Backend service overloaded")
print("5. Long-running PDF processing (>5 min)")
print("6. Network timeouts to external APIs")
print("=" * 80)

# 6. Quick test of async processing
print("\n6. Testing async processing...")
async def test_async():
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    processor = UnifiedCitationProcessorV2()
    
    # Small test text
    test_text = "This is a test citation: 123 U.S. 456 (2023)."
    
    start_time = time.time()
    try:
        result = await processor.process_text_async(test_text)
        elapsed = time.time() - start_time
        print(f"✅ Async processing completed in {elapsed:.2f} seconds")
        print(f"   Found {len(result.get('citations', []))} citations")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Async processing failed after {elapsed:.2f} seconds")
        print(f"   Error: {e}")

try:
    asyncio.run(test_async())
except Exception as e:
    print(f"Could not test async processing: {e}")
