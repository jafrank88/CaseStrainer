"""
Check production results from Redis
"""
from redis import Redis
from rq.job import Job

# Connect to Redis
r = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')

# Fetch job
job_id = '8aa939e6-4321-4aae-9f30-71e9924befd5'
job = Job.fetch(job_id, connection=r)

result = job.result
citations = result.get('result', {}).get('citations', [])

total = len(citations)
with_names = 0
without_names = 0

examples_with = []
examples_without = []

for c in citations:
    case_name = c.get('extracted_case_name', '')
    if case_name and case_name.strip() and case_name != 'N/A':
        with_names += 1
        if len(examples_with) < 5:
            examples_with.append({
                'citation': c.get('citation'),
                'name': case_name
            })
    else:
        without_names += 1
        if len(examples_without) < 5:
            examples_without.append({
                'citation': c.get('citation'),
                'name': case_name if case_name else '(empty)'
            })

print('='*80)
print('PRODUCTION EXTRACTION TEST RESULTS')
print('='*80)
print(f'Total citations: {total}')
print(f'With case names: {with_names} ({with_names/total*100:.1f}%)')
print(f'Without case names: {without_names} ({without_names/total*100:.1f}%)')

print('\n' + '='*80)
print('EXAMPLES WITH NAMES (First 5):')
print('='*80)
for i, ex in enumerate(examples_with, 1):
    print(f'{i}. {ex["citation"]}')
    print(f'   → {ex["name"]}')

print('\n' + '='*80)
print('EXAMPLES WITHOUT NAMES (First 5):')
print('='*80)
for i, ex in enumerate(examples_without, 1):
    print(f'{i}. {ex["citation"]}')
    print(f'   → {ex["name"]}')
