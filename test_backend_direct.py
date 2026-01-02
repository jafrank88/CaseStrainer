import requests
import time

# Test backend with the problematic PDF
url = 'https://www.courts.wa.gov/opinions/pdf/1033397.pdf'
target_citations = ['180 Wn.2d 515', '179 Wn.2d 376', '114 Wn.2d 213']

print(f"Testing backend with: {url}")
r = requests.post('http://127.0.0.1:5000/casestrainer/api/analyze', 
                  json={'url': url}, timeout=60)
data = r.json()
task_id = data.get('task_id')
print(f"Task ID: {task_id}")
print(f"Initial status: {data.get('status')}")

# Poll for results
for i in range(60):
    time.sleep(3)
    r2 = requests.get(f'http://127.0.0.1:5000/casestrainer/api/status/{task_id}', timeout=30)
    status_data = r2.json()
    status = status_data.get('status')
    print(f"Poll {i+1}: {status}")
    if status == 'completed':
        cits = status_data.get('citations', [])
        print(f"\nTotal citations: {len(cits)}")
        target = [c for c in cits if c.get('citation') in target_citations]
        print(f"\nTarget citations ({len(target)}):")
        for c in target:
            print(f"  {c['citation']}: extracted='{c.get('extracted_case_name')}'")
        break
    elif status == 'failed':
        print('Failed:', status_data.get('error'))
        break
