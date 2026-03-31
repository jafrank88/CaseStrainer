import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:437abc17-8699-45d4-91f8-5058525ea129:result')
if result:
    d = json.loads(result)
    clusters = d.get('clusters', [])
    print(f"Total clusters: {len(clusters)}")
    print("\nChecking for bad clusters (same reporter, different volumes):")
    bad_count = 0
    for c in clusters:
        if c.get('size', 0) > 1:
            members = c.get('cluster_members', [])
            us_volumes = set()
            has_placeholder = any('____' in m or '___' in m for m in members)
            for m in members:
                if ' U.S. ' in m:
                    try:
                        vol = m.split(' U.S. ')[0].strip()
                        us_volumes.add(vol)
                    except:
                        pass
            if len(us_volumes) > 1 or has_placeholder:
                bad_count += 1
                name = c.get('case_name', 'N/A')[:40]
                placeholder_flag = " [HAS PLACEHOLDER]" if has_placeholder else ""
                print(f"  BAD: {name} - volumes: {us_volumes}{placeholder_flag}")
                print(f"       Members: {members}")
    if bad_count == 0:
        print("  ✓ NO BAD CLUSTERS FOUND!")
    else:
        print(f"\n  Found {bad_count} bad clusters")
else:
    print("Result not ready yet")
