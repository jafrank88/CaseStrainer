import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:43c94035-a13b-4402-a979-647b139a279c:result')
if result:
    d = json.loads(result)
    citations = d.get('citations', [])
    clusters = d.get('clusters', [])
    
    print(f"Total citations: {len(citations)}")
    print(f"Total clusters: {len(clusters)}")
    
    # Check for Steel Co and Sprint Communications
    print("\n--- Looking for Steel Co and Sprint Communications ---")
    steel_sprint = []
    for c in citations:
        cit_text = c.get('citation', '')
        if '523 U.S. 83' in cit_text or '554 U.S. 269' in cit_text:
            name = c.get('case_name', c.get('canonical_name', 'N/A'))[:50]
            verified = '✓ VERIFIED' if c.get('verified') else '✗ UNVERIFIED'
            parallel = ' (Verified by Parallel)' if c.get('true_by_parallel') else ''
            print(f"  {cit_text}: {verified}{parallel} - {name}")
            steel_sprint.append(c)
    
    # Check if they're in the same cluster
    print("\n--- Checking clusters for these citations ---")
    for cluster in clusters:
        members = cluster.get('cluster_members', [])
        has_523 = any('523 U.S. 83' in (m.get('citation', m) if isinstance(m, dict) else m) for m in members)
        has_554 = any('554 U.S. 269' in (m.get('citation', m) if isinstance(m, dict) else m) for m in members)
        if has_523 and has_554:
            print(f"  PROBLEM: Both citations in same cluster!")
            print(f"    Cluster name: {cluster.get('case_name', 'N/A')[:50]}")
            print(f"    Members: {members}")
        elif has_523 or has_554:
            name = cluster.get('case_name', 'N/A')[:50]
            print(f"  Found cluster with one citation: {name}")
    
    if not any('523 U.S. 83' in str(m) for cluster in clusters for m in cluster.get('cluster_members', [])):
        print("  Note: 523 U.S. 83 not found in any cluster (may be standalone)")
    if not any('554 U.S. 269' in str(m) for cluster in clusters for m in cluster.get('cluster_members', [])):
        print("  Note: 554 U.S. 269 not found in any cluster (may be standalone)")
    
    # Check for bad clusters (same reporter, different volumes)
    print("\n--- Checking for bad clusters ---")
    bad_count = 0
    for c in clusters:
        if c.get('size', 0) > 1:
            members = c.get('cluster_members', [])
            us_volumes = set()
            for m in members:
                m_str = m.get('citation', m) if isinstance(m, dict) else m
                if ' U.S. ' in str(m_str):
                    try:
                        vol = str(m_str).split(' U.S. ')[0].strip()
                        us_volumes.add(vol)
                    except:
                        pass
            if len(us_volumes) > 1:
                bad_count += 1
                name = c.get('case_name', 'N/A')[:40]
                print(f"  BAD: {name} - volumes: {us_volumes}")
    
    if bad_count == 0:
        print("  ✓ No bad clusters found!")
else:
    print("Result not ready yet")
