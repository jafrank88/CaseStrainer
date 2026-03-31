import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:ce4b748b-0da7-4fb3-89b7-752d49eced66:result')
if result:
    d = json.loads(result)
    clusters = d.get('clusters', [])
    print(f"Total clusters: {len(clusters)}")
    print("\nClusters with multiple citations:")
    for c in clusters:
        size = c.get('size', 0)
        if size > 1:
            name = c.get('case_name', 'N/A')[:50]
            members = c.get('cluster_members', [])
            print(f"\nCluster: {name}")
            print(f"  Size: {size}")
            print(f"  Members: {members}")
else:
    print("Result not ready yet")
