import redis, os, json, sys
sys.path.insert(0, '/app')

r = redis.from_url(os.getenv('REDIS_URL'))
keys = sorted([k for k in r.keys('rq:job:*:result') if b'function' not in k])
print('Found', len(keys), 'jobs')

for k in keys[-2:]:
    print('\nJob:', k.decode())
    res = r.get(k)
    if not res:
        continue
    try:
        d = json.loads(res)
        cites = d.get('citations', [])
        for c in cites:
            cn = str(c.get('case_name', ''))
            ecn = str(c.get('extracted_case_name', ''))
            if 'Swin' in cn or 'Swin' in ecn or 'Chalk' in cn or 'Chalk' in ecn:
                print(f"  {c.get('citation')}: case_name='{cn}' extracted='{ecn}'")
                print(f"    verified={c.get('verified')} url={bool(c.get('canonical_url'))}")
    except Exception as e:
        print('Error:', e)
