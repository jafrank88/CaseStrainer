#!/usr/bin/env python3
"""
Inspect the actual job result in detail
"""
import sys
from redis import Redis
from rq.job import Job
import json

if len(sys.argv) < 2:
    print("Usage: python inspect_job_result.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]

redis_conn = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')

print("="*60)
print(f"DETAILED JOB RESULT INSPECTION")
print("="*60)

try:
    job = Job.fetch(job_id, connection=redis_conn)
    result = job.result
    
    if not isinstance(result, dict):
        print(f"Result is not a dict: {type(result)}")
        print(result)
        sys.exit(1)
    
    # Check what we got
    print(f"\n1. BASIC STATS:")
    print(f"   Success: {result.get('success')}")
    print(f"   Citations count: {len(result.get('citations', []))}")
    print(f"   Clusters count: {len(result.get('clusters', []))}")
    
    # Check verification
    citations = result.get('citations', [])
    if citations:
        verified_count = sum(1 for c in citations if c.get('verified'))
        print(f"\n2. VERIFICATION:")
        print(f"   Verified: {verified_count}/{len(citations)}")
        
        # Show first 3 citations
        print(f"\n3. FIRST 3 CITATIONS:")
        for i, cit in enumerate(citations[:3], 1):
            print(f"\n   Citation {i}:")
            print(f"     Text: {cit.get('citation')}")
            print(f"     Case: {cit.get('extracted_case_name', 'N/A')}")
            print(f"     Verified: {cit.get('verified', False)}")
            if cit.get('canonical_name'):
                print(f"     Canonical: {cit.get('canonical_name')}")
    
    # Check clusters structure
    clusters = result.get('clusters', [])
    if clusters:
        print(f"\n4. CLUSTERS STRUCTURE:")
        print(f"   Total clusters: {len(clusters)}")
        
        # Check first cluster
        if len(clusters) > 0:
            cluster = clusters[0]
            print(f"\n   First cluster keys: {list(cluster.keys())}")
            print(f"   Citations in first cluster: {len(cluster.get('citations', []))}")
            
            # Are clusters actually just citations?
            if 'citation' in cluster:
                print(f"\n   ⚠️  WARNING: Clusters look like citations!")
                print(f"   Cluster has 'citation' field: {cluster.get('citation')}")
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
