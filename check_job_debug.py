#!/usr/bin/env python
"""Debug the job processing to see what's happening."""

import requests
import json

# Check both jobs
jobs = [
    ("PDF with verification", "0d5cc3e1-bd5b-4d74-964a-a95dd3a6518e"),
    ("PDF extraction only", "ebbfed49-770c-447d-871f-bde4808777aa")
]

print("=" * 80)
print("JOB STATUS DEBUG")
print("=" * 80)

for name, task_id in jobs:
    print(f"\n{name}:")
    print(f"Task ID: {task_id}")
    
    url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
    
    try:
        response = requests.get(url)
        status = response.json()
        
        print(f"Status: {status.get('status')}")
        print(f"Progress: {status.get('verification_status', {}).get('progress_percent', 0)}%")
        print(f"Message: {status.get('verification_status', {}).get('current_message', 'N/A')}")
        
        # Check if result is available even if status isn't 'completed'
        if 'result' in status:
            result = status['result']
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"⚠️  RESULT AVAILABLE BUT STATUS NOT COMPLETED:")
            print(f"  Citations: {len(citations)}")
            print(f"  Clusters: {len(clusters)}")
            
            # Show first few
            if citations:
                print(f"  First 3 citations:")
                for i, cit in enumerate(citations[:3]):
                    print(f"    {i+1}. {cit.get('citation', 'N/A')}")
        
        # Check metadata
        if 'metadata' in status:
            metadata = status['metadata']
            print(f"Metadata:")
            for key, value in metadata.items():
                if key not in ['processing_time_ms']:
                    print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")

# Check Redis queue directly
print(f"\n" + "=" * 80)
print("REDIS QUEUE STATUS")
print("=" * 80)

import subprocess
try:
    result = subprocess.run(
        ['docker', 'exec', 'casestrainer-redis-prod', 'redis-cli', '-a', '***REDACTED_REDIS_PASSWORD***', 'llen', 'casestrainer'],
        capture_output=True, text=True
    )
    print(f"Queue length: {result.stdout.strip()}")
except:
    print("Could not check Redis queue")

# Check worker status
print(f"\n" + "=" * 80)
print("WORKER STATUS")
print("=" * 80)

try:
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=worker', '--format', 'table {{.Names}}\t{{.Status}}'],
        capture_output=True, text=True
    )
    print(result.stdout)
except:
    print("Could not check worker status")
