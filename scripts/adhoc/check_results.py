import redis, json, os
r = redis.from_url(os.getenv('REDIS_URL'))
d = json.loads(r.get('rq:job:38c1b954-4e0b-46d4-8167-c611bd1ab5ad:result'))
c = d.get('citations', [])
print('Total citations:', len(c))
v = sum(1 for x in c if x.get('verified'))
print('Verified:', v)
print('Unverified:', len(c) - v)
print('\nFirst 10 citations:')
for i, x in enumerate(c[:10]):
    name = x.get('case_name', 'N/A')[:40]
    print(f"  {i+1}. {x['citation']}: verified={x.get('verified')}, name={name}")
