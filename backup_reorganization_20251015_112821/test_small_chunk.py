import requests
import PyPDF2

# Extract first 4KB (under 5KB threshold for sync)
pdf = open('24-2626.pdf', 'rb')
reader = PyPDF2.PdfReader(pdf)
text = ''.join([p.extract_text() for p in reader.pages])
chunk = text[:4000]

print(f"Sending {len(chunk)} chars (should trigger sync)")

response = requests.post(
    'http://localhost:5000/casestrainer/api/analyze',
    json={'text': chunk},
    timeout=120
)

result = response.json()
citations = result.get('citations', [])
mode = result.get('metadata', {}).get('processing_mode', 'unknown')

print(f"Processing mode: {mode}")
print(f"Citations found: {len(citations)}\n")

for i, c in enumerate(citations[:15], 1):
    cite_text = c.get('citation', '')
    case_name = c.get('extracted_case_name', 'N/A')
    cluster_id = c.get('cluster_id', 'none')
    print(f"{i:2}. {cite_text:20} -> {case_name:40} (cluster: {cluster_id})")
