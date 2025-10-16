import subprocess
import sys

# Check worker logs for recent activity
workers = ['casestrainer-rqworker1-prod', 'casestrainer-rqworker2-prod', 'casestrainer-rqworker3-prod']

for worker in workers:
    print(f"\n{'='*60}")
    print(f"Worker: {worker}")
    print('='*60)
    
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail=30', worker],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.split('\n')
        
        # Filter for important messages
        for line in lines:
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in ['job', 'processing', 'error', 'fail', 'task', 'listen']):
                print(line)
                
    except Exception as e:
        print(f"Error checking {worker}: {e}")

# Also check Redis connection from worker
print(f"\n{'='*60}")
print("Testing Redis Connection from Worker")
print('='*60)

try:
    result = subprocess.run(
        ['docker', 'exec', 'casestrainer-rqworker1-prod', 'python', '-c',
         'import redis; r = redis.Redis(host="casestrainer-redis-prod", port=6379, password="***REDACTED_REDIS_PASSWORD***"); print("✅ Redis ping:", r.ping()); from rq import Queue; q = Queue("casestrainer", connection=r); print("✅ Queue length:", len(q)); print("✅ Worker count:", q.count)'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print("Error:", result.stderr)
        
except Exception as e:
    print(f"Error: {e}")
