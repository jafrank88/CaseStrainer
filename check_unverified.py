import requests
import re

# Upload the PDF file
url = "http://localhost:5000/casestrainer/api/analyze"
files = {'file': open('D:/dev/casestrainer/motion.pdf', 'rb')}
data = {'force_mode': 'sync'}

print("Uploading motion.pdf to backend...")
response = requests.post(url, files=files, data=data, timeout=300)

if response.status_code == 200:
    result = response.json()
    
    print("\n=== Unverified Non-WL Citations ===")
    for cit in result.get('citations', []):
        citation_text = cit.get('citation', '')
        verified = cit.get('verified')
        
        # Skip WL citations and verified citations
        if 'WL' in citation_text or verified:
            continue
        
        # Check if it's a Federal Reporter citation
        is_federal = bool(re.search(r'\b\d+\s+F\.(2d|3d|4th)\s+\d+', citation_text))
        is_frd = bool(re.search(r'\b\d+\s+F\.R\.D\.\s+\d+', citation_text))
        
        print(f"\nCitation: {citation_text}")
        print(f"  Type: {'Federal Reporter' if is_federal else 'F.R.D.' if is_frd else 'Other'}")
        print(f"  Extracted Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"  Extracted Date: {cit.get('extracted_date', 'N/A')}")
        print(f"  Source: {cit.get('source', 'N/A')}")
        print(f"  Error: {cit.get('error', 'None')}")
