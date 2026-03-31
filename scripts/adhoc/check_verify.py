import redis, json, os

r = redis.from_url(os.getenv('REDIS_URL'))
result = r.get('rq:job:30c3275e-3a69-4557-ab08-7add42cfe444:result')
if result:
    d = json.loads(result)
    citations = d.get('citations', [])
    print(f"Total citations: {len(citations)}")
    print("\nVerified citations count:", sum(1 for c in citations if c.get('verified')))
    print("Unverified:", sum(1 for c in citations if not c.get('verified')))
    
    print("\n--- Key citations from the problematic clusters ---")
    target_cites = ['578 U.S. 330', '594 U.S. ____', '497 U.S. 1', '523 U.S. 83', '554 U.S. 269']
    for c in citations:
        cit_text = c.get('citation', '')
        if any(t in cit_text for t in target_cites):
            verified = c.get('verified', False)
            v_status = "✓ VERIFIED" if verified else "✗ UNVERIFIED"
            name = c.get('case_name', 'N/A')[:50]
            print(f"  {cit_text}: {v_status} - {name}")
else:
    print("Result not ready")
