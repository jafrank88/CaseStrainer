import redis
import json

r = redis.Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6379/0')

task_id = "ddc1dd94-cb04-45ca-8a54-9cc393c14dc2"

# Get job data
job_key = f"rq:job:{task_id}"
job_data = r.hgetall(job_key)

print("🔍 Job Data Keys:")
for key in job_data.keys():
    print(f"  - {key.decode()}")

# Get status
status = job_data.get(b'status', b'unknown').decode()
print(f"\n📊 Status: {status}")

# Get result
result_key = f"rq:results:{task_id}"
result_data = r.get(result_key)

if result_data:
    result = json.loads(result_data)
    print(f"\n✅ Result exists!")
    print(f"  - Success: {result.get('success')}")
    print(f"  - Status: {result.get('status')}")
    
    if 'result' in result:
        inner_result = result['result']
        if isinstance(inner_result, dict):
            citations = inner_result.get('citations', [])
            clusters = inner_result.get('clusters', [])
            
            print(f"\n📝 Citations: {len(citations)}")
            print(f"📚 Clusters: {len(clusters)}")
            
            # Show cluster sizes
            for idx, cluster in enumerate(clusters, 1):
                size = cluster.get('size', 0)
                case_name = cluster.get('case_name', 'Unknown')
                print(f"\nCluster {idx}: {case_name} (size: {size})")
                if size > 1:
                    members = cluster.get('cluster_members', [])
                    for member in members:
                        print(f"  - {member}")
        else:
            print(f"\n⚠️  Inner result is not a dict: {type(inner_result)}")
    
    # Save full result
    with open('job_result_details.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full result saved to job_result_details.json")
else:
    print(f"\n❌ No result data found!")
