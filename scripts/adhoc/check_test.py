import json, os, redis

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:70a0d9c5-6d1b-4821-b8af-edbef5944b18:result')
if result:
    d = json.loads(result)
    clusters = d.get('clusters', [])
    print(f"Total clusters: {len(clusters)}")
    print("\nChecking for bad clusters:")
    bad_count = 0
    for c in clusters:
        if c.get('size', 0) > 1:
            members = c.get('cluster_members', [])
            us_volumes = set()
            for m in members:
                if ' U.S. ' in m:
                    try:
                        vol = m.split(' U.S. ')[0].strip()
                        us_volumes.add(vol)
                    except:
                        pass
            if len(us_volumes) > 1:
                bad_count += 1
                name = c.get('case_name', 'N/A')[:40]
                print(f"  BAD: {name} - volumes: {us_volumes}")
    if bad_count == 0:
        print("  NO BAD CLUSTERS FOUND!")
    else:
        print(f"\n  Found {bad_count} bad clusters")
else:
    print("Result not ready yet")
