import redis
import json

r = redis.Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')

task_id = "ddc1dd94-cb04-45ca-8a54-9cc393c14dc2"
result_data = r.get(f'rq:results:{task_id}')

if result_data:
    result = json.loads(result_data)
    print(f"SUCCESS: {result.get('success')}")
    print(f"STATUS: {result.get('status')}")
    
    if 'result' in result and isinstance(result['result'], dict):
        clusters = result['result'].get('clusters', [])
        citations = result['result'].get('citations', [])
        print(f"CLUSTERS: {len(clusters)}")
        print(f"CITATIONS: {len(citations)}")
        
        for idx, cluster in enumerate(clusters, 1):
            size = cluster.get('size', 0)
            members = cluster.get('cluster_members', [])
            case_name = cluster.get('case_name', 'Unknown')
            print(f"  Cluster {idx}: size={size}, members={len(members)}, name={case_name[:50]}")
else:
    print("NO RESULT")
