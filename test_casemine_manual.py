"""Test manual CaseMine access to understand URL patterns"""
import requests
import re

# Test what happens when we search manually
citation = "11 F.4th 1133"
case_name = "Alam v. Garland"

# Try different search approaches
tests = [
    ("Quoted citation", f'https://www.casemine.com/search?q="{citation}"'),
    ("Unquoted citation", f'https://www.casemine.com/search?q={citation.replace(" ", "+")}'),
    ("Case name + citation", f'https://www.casemine.com/search?q={case_name.replace(" ", "+")}+{citation.replace(" ", "+")}'),
    ("Just case name", f'https://www.casemine.com/search?q={case_name.replace(" ", "+")}'),
]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

for test_name, url in tests:
    print(f"\n{'='*80}")
    print(f"Test: {test_name}")
    print(f"URL: {url}")
    print("-"*80)
    
    try:
        resp = session.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)}")
        
        # Look for judgment/judgement links
        judgment_pattern = r'href="([^"]*(?:judgment|judgement)[^"]*)"'
        matches = re.findall(judgment_pattern, resp.text, re.IGNORECASE)
        print(f"Judgment links found: {len(matches)}")
        
        if matches:
            print(f"\nFirst 3 links:")
            for i, link in enumerate(matches[:3]):
                print(f"  {i+1}. {link}")
        
        # Look for case names in results
        case_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        case_matches = re.findall(case_pattern, resp.text)
        if case_matches:
            unique_cases = list(set(case_matches))[:5]
            print(f"\nCase names found: {len(unique_cases)}")
            for case in unique_cases:
                print(f"  - {case}")
                
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n{'='*80}")
print("Analysis complete")
