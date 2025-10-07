from redis import Redis
from rq.job import Job

r = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
job = Job.fetch('8e400a9a-36f8-40fa-9b29-15015dcd1976', connection=r)
result = job.result
citations = result.get('result', {}).get('citations', [])

print('='*80)
print('EXTRACTION ANALYSIS')
print('='*80)

# Count categories
empty = [c for c in citations if not c.get('extracted_case_name') or c.get('extracted_case_name') == '']
null = [c for c in citations if c.get('extracted_case_name') is None]
na = [c for c in citations if c.get('extracted_case_name') == 'N/A']
truncated = [c for c in citations if c.get('extracted_case_name') and 
             (c.get('extracted_case_name').startswith(('Inc.', 'LLC', 'Corp.')) or 
              len(c.get('extracted_case_name')) < 15)]
good = [c for c in citations if c.get('extracted_case_name') and 
        c.get('extracted_case_name') != 'N/A' and 
        len(c.get('extracted_case_name')) >= 15]

print(f'\nTotal citations: {len(citations)}')
print(f'Empty string: {len(empty)}')
print(f'Null: {len(null)}')
print(f'N/A: {len(na)}')
print(f'Truncated: {len(truncated)}')
print(f'Good extractions: {len(good)}')

print('\n' + '='*80)
print('EXAMPLES OF EMPTY/NULL (first 5):')
print('='*80)
for c in (empty + null)[:5]:
    print(f"Citation: {c.get('citation')}")
    print(f"  Extracted: '{c.get('extracted_case_name')}'")
    print(f"  Canonical: {c.get('canonical_name')}")
    print()

print('='*80)
print('EXAMPLES OF TRUNCATED (first 5):')
print('='*80)
for c in truncated[:5]:
    print(f"Citation: {c.get('citation')}")
    print(f"  Extracted: '{c.get('extracted_case_name')}'")
    print(f"  Canonical: {c.get('canonical_name')}")
    print()
