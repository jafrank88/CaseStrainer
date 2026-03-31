import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:a00c2a21-0bbd-42c7-8193-3b0216dd8130:result')
if result:
    d = json.loads(result)
    clusters = d.get('clusters', [])
    print(f"Total clusters: {len(clusters)}")
    print("\nClusters with multiple citations:")
    found_us_clusters = False
    for c in clusters:
        size = c.get('size', 0)
        if size > 1:
            name = c.get('case_name', 'N/A')[:50]
            members = c.get('cluster_members', [])
            # Check if any are U.S. citations with different volumes
            us_volumes = set()
            for m in members:
                if ' U.S. ' in m:
                    try:
                        vol = m.split(' U.S. ')[0].strip()
                        us_volumes.add(vol)
                    except:
                        pass
            if len(us_volumes) > 1:
                found_us_clusters = True
                print(f"\n*** SAME REPORTER CLUSTER (BAD): {name}")
                print(f"    Members: {members}")
                print(f"    U.S. Volumes: {us_volumes}")
            else:
                print(f"\nCluster: {name}")
                print(f"  Members: {members}")
    if not found_us_clusters:
        print("\n✓ No same-reporter/different-volume clusters found!")
else:
    print("Result not ready yet")
