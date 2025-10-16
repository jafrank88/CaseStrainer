"""
Test the Grace v. Perkins Restaurant case from CourtListener
Compare actual citations in the opinion vs what our system extracts
"""

import requests
from src.config import COURTLISTENER_API_KEY

print("="*80)
print("GRACE V. PERKINS RESTAURANT - CITATION EXTRACTION TEST")
print("="*80)

# Step 1: Get the actual opinion from CourtListener API
opinion_id = "10320728"
api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"

print(f"\n1. Fetching opinion from CourtListener API...")
print(f"   URL: {api_url}")

headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'Accept': 'application/json'
}

response = requests.get(api_url, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error fetching opinion: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
    exit(1)

data = response.json()

# Extract the opinion text
opinion_text = None
if 'plain_text' in data:
    opinion_text = data['plain_text']
    source = 'plain_text'
elif 'html_with_citations' in data:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(data['html_with_citations'], 'html.parser')
    opinion_text = soup.get_text(separator=' ', strip=True)
    source = 'html_with_citations'
elif 'html' in data:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(data['html'], 'html.parser')
    opinion_text = soup.get_text(separator=' ', strip=True)
    source = 'html'
else:
    print(f"   Error: No text content found in API response")
    print(f"   Available fields: {list(data.keys())}")
    exit(1)

print(f"   ✓ Extracted {len(opinion_text):,} characters from '{source}'")

# Get case metadata
case_name = data.get('case_name', 'N/A')
date_filed = data.get('date_filed', 'N/A')
print(f"\n   Case: {case_name}")
print(f"   Date: {date_filed}")

# Step 2: Look for specific citation patterns in the raw text
print(f"\n2. Searching for citation patterns in raw text...")
import re

# Dash-separated Ohio citations
dash_ohio = re.findall(r'\b\d{1,5}-Ohio(?:\s*St\.)?(?:\s*\d[a-z]{0,2})?-\d{1,12}\b', opinion_text, re.IGNORECASE)
print(f"   Dash-separated Ohio citations: {len(dash_ohio)}")
if dash_ohio:
    for cit in dash_ohio[:5]:
        print(f"     - {cit}")

# Space-separated Ohio citations
space_ohio = re.findall(r'\b\d{1,5}\s+Ohio(?:\s+St\.)?(?:\s+\d[a-z]{0,2})?\s+\d{1,12}\b', opinion_text, re.IGNORECASE)
print(f"   Space-separated Ohio citations: {len(space_ohio)}")
if space_ohio:
    for cit in space_ohio[:5]:
        print(f"     - {cit}")

# Federal citations
federal = re.findall(r'\b\d{1,5}\s+F\.\s*(?:\d*(?:st|nd|rd|th|d))?\s*\d{1,12}\b', opinion_text)
print(f"   Federal Reporter citations: {len(federal)}")
if federal:
    for cit in federal[:5]:
        print(f"     - {cit}")

# U.S. Supreme Court
us_reports = re.findall(r'\b\d{1,5}\s+U\.S\.\s+\d{1,12}\b', opinion_text)
print(f"   U.S. Reports citations: {len(us_reports)}")
if us_reports:
    for cit in us_reports[:5]:
        print(f"     - {cit}")

# Step 3: Process with our system
print(f"\n3. Processing with CaseStrainer extraction pipeline...")
print(f"   Saving opinion text to temp file for processing...")

# Save to temp file
import tempfile
import os

temp_file = os.path.join(tempfile.gettempdir(), 'grace_perkins_opinion.txt')
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(opinion_text)

print(f"   Saved to: {temp_file}")

# Extract citations using our pipeline
from src.citation_extraction_endpoint import extract_citations_with_clustering

print(f"\n   Running extraction pipeline...")
result = extract_citations_with_clustering(opinion_text, enable_verification=False)

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print(f"   ✓ Extraction complete")
print(f"   Total citations found: {len(citations)}")
print(f"   Clusters: {len(clusters)}")

# Step 4: Compare results
print(f"\n4. COMPARISON: Manual Search vs CaseStrainer")
print("="*80)

total_manual = len(dash_ohio) + len(space_ohio) + len(federal) + len(us_reports)
print(f"   Manual regex search: {total_manual} citations")
print(f"     - Dash Ohio: {len(dash_ohio)}")
print(f"     - Space Ohio: {len(space_ohio)}")
print(f"     - Federal: {len(federal)}")
print(f"     - U.S. Reports: {len(us_reports)}")

print(f"\n   CaseStrainer pipeline: {len(citations)} citations")

# Show sample of extracted citations
print(f"\n5. Sample of CaseStrainer extractions (first 10):")
print("-"*80)
for i, cit in enumerate(citations[:10], 1):
    citation_text = cit.get('citation', 'N/A')
    case_name = cit.get('extracted_case_name', 'N/A')
    date = cit.get('extracted_date', 'N/A')
    print(f"{i:2}. {citation_text:30} | {case_name[:40]:40} | {date}")

# Check for dash-separated citations in results
dash_found = [c for c in citations if '-' in c.get('citation', '') and 'Ohio' in c.get('citation', '')]
print(f"\n6. Dash-separated Ohio citations found by CaseStrainer: {len(dash_found)}")
if dash_found:
    for cit in dash_found:
        print(f"   ✓ {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')}")
else:
    print(f"   ✗ None found (may need to check if they're normalized)")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
