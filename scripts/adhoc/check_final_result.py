import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:5a32ed05-d6f4-44b6-822b-71db1b389f12:result')
if result:
    d = json.loads(result)
    citations = d.get('citations', [])
    clusters = d.get('clusters', [])
    
    print(f"Total citations: {len(citations)}")
    print(f"Total clusters: {len(clusters)}")
    
    # Check verification stats
    verified = sum(1 for c in citations if c.get('verified'))
    print(f"\nVerified citations: {verified}")
    print(f"Unverified: {len(citations) - verified}")
    
    # Check for bad clusters
    print("\n--- Checking clusters ---")
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
                print(f"  BAD: {name}")
                print(f"       Members: {members}")
    
    if bad_count == 0:
        print("  ✓ No bad clusters found!")
    else:
        print(f"  Found {bad_count} bad clusters")
    
    # Show sample verified citations
    print("\n--- Sample Verified Citations ---")
    for c in citations[:10]:
        if c.get('verified'):
            print(f"  {c['citation']}: {c.get('case_name', 'N/A')[:40]}")
else:
    print("Result not ready yet")
