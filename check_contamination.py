from redis import Redis
from rq.job import Job

r = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
job = Job.fetch('1c24fb6f-f143-4642-be12-19375aa0af8a', connection=r)
result = job.result
citations = result.get('result', {}).get('citations', [])

print('='*80)
print('CONTAMINATION CHECK')
print('='*80)

identical_count = 0
different_count = 0

print('\nFirst 10 citations:')
for c in citations[:10]:
    extracted = c.get('extracted_case_name', '')
    canonical = c.get('canonical_name', '')
    is_identical = extracted == canonical
    
    if is_identical:
        identical_count += 1
    else:
        different_count += 1
    
    print(f"\nCitation: {c.get('citation')}")
    print(f"  Extracted: '{extracted}'")
    print(f"  Canonical: '{canonical}'")
    print(f"  Identical: {is_identical}")

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
total = len(citations)
identical_all = sum(1 for c in citations if c.get('extracted_case_name') == c.get('canonical_name'))
print(f'Total citations: {total}')
print(f'Identical extracted/canonical: {identical_all} ({round(identical_all/total*100, 1)}%)')
print(f'Different extracted/canonical: {total - identical_all} ({round((total-identical_all)/total*100, 1)}%)')
