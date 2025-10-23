#!/bin/bash
task_id="ddc1dd94-cb04-45ca-8a54-9cc393c14dc2"

python3 << 'EOF'
import redis
import json
import sys

r = redis.Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')

task_id = "ddc1dd94-cb04-45ca-8a54-9cc393c14dc2"

# Get result
result_key = f"rq:results:{task_id}"
result_data = r.get(result_key)

if result_data:
    result = json.loads(result_data)
    print("SUCCESS:", result.get('success'))
    print("STATUS:", result.get('status'))
    
    if 'result' in result:
        inner_result = result['result']
        if isinstance(inner_result, dict):
            citations = inner_result.get('citations', [])
            clusters = inner_result.get('clusters', [])
            
            print(f"CITATIONS: {len(citations)}")
            print(f"CLUSTERS: {len(clusters)}")
            
            for idx, cluster in enumerate(clusters, 1):
                size = cluster.get('size', 0)
                case_name = cluster.get('case_name', 'Unknown')
                members = cluster.get('cluster_members', [])
                print(f"Cluster {idx}: {case_name} | Size: {size} | Members: {len(members)}")
    
    print("\n=== FULL RESULT ===")
    print(json.dumps(result, indent=2))
else:
    print("NO RESULT FOUND")
    sys.exit(1)
EOF
