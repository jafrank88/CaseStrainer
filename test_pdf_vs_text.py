"""
Test to compare PDF extraction vs text file extraction
"""
import requests
import json

api_url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 80)
print("TESTING PDF vs TEXT EXTRACTION")
print("=" * 80)

# Test 1: Text file
print("\n1. Testing with extracted text file...")
with open('1033940_extracted.txt', 'r', encoding='utf-8') as f:
    text_content = f.read()

text_payload = {
    "type": "text",
    "text": text_content
}

try:
    response = requests.post(api_url, json=text_payload, timeout=120)
    text_data = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Success: {text_data.get('success')}")
    print(f"   Citations: {len(text_data.get('citations', []))}")
    print(f"   Clusters: {len(text_data.get('clusters', []))}")
    
    text_citations = text_data.get('citations', [])
    print(f"\n   First 5 citations:")
    for i, cit in enumerate(text_citations[:5], 1):
        print(f"     {i}. {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    text_citations = []

# Test 2: PDF file
print("\n2. Testing with PDF file...")
pdf_payload = {
    "type": "url",
    "url": "file:///d:/dev/casestrainer/1033940.pdf"
}

try:
    response = requests.post(api_url, json=pdf_payload, timeout=120)
    pdf_data = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Success: {pdf_data.get('success')}")
    print(f"   Citations: {len(pdf_data.get('citations', []))}")
    print(f"   Clusters: {len(pdf_data.get('clusters', []))}")
    
    pdf_citations = pdf_data.get('citations', [])
    if pdf_citations:
        print(f"\n   First 5 citations:")
        for i, cit in enumerate(pdf_citations[:5], 1):
            print(f"     {i}. {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    pdf_citations = []

# Test 3: PDF URL (original test)
print("\n3. Testing with PDF URL...")
pdf_url_payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

try:
    response = requests.post(api_url, json=pdf_url_payload, timeout=120)
    pdf_url_data = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Success: {pdf_url_data.get('success')}")
    print(f"   Citations: {len(pdf_url_data.get('citations', []))}")
    print(f"   Clusters: {len(pdf_url_data.get('clusters', []))}")
    
    pdf_url_citations = pdf_url_data.get('citations', [])
    if pdf_url_citations:
        print(f"\n   First 5 citations:")
        for i, cit in enumerate(pdf_url_citations[:5], 1):
            print(f"     {i}. {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    pdf_url_citations = []

# Comparison
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)
print(f"\nText file:    {len(text_citations)} citations")
print(f"PDF file:     {len(pdf_citations)} citations")
print(f"PDF URL:      {len(pdf_url_citations)} citations")

if len(text_citations) > 0 and len(pdf_citations) == 0:
    print("\n❌ ISSUE: PDF extraction not working (text works)")
elif len(text_citations) == len(pdf_citations):
    print("\n✅ SUCCESS: PDF and text return same number of citations")
else:
    print(f"\n⚠️  MISMATCH: Different citation counts")

print("\n" + "=" * 80)
