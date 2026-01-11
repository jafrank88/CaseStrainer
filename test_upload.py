import requests
import time

# Upload the PDF file
url = "http://localhost:5000/casestrainer/api/analyze"
files = {'file': open('D:/dev/casestrainer/motion.pdf', 'rb')}
data = {'force_mode': 'sync'}

print("Uploading motion.pdf to backend...")
start = time.time()
response = requests.post(url, files=files, data=data, timeout=300)
elapsed = time.time() - start

print(f"\nResponse Status: {response.status_code}")
print(f"Processing Time: {elapsed:.1f}s")
print(f"\nResponse Length: {len(response.text)} chars")

if response.status_code == 200:
    result = response.json()
    print(f"\nCitations Found: {len(result.get('citations', []))}")
    print(f"Clusters Found: {len(result.get('clusters', []))}")
    
    # Count verified vs unverified
    citations = result.get('citations', [])
    verified = sum(1 for c in citations if c.get('verified'))
    print(f"Verified: {verified}/{len(citations)}")
else:
    print(f"\nError: {response.text[:500]}")
