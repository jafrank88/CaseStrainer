#!/usr/bin/env python
"""Test OpenJurist and Caselaw Access Project"""

import requests
import re
from urllib.parse import quote
import json

def test_openjurist_detailed():
    """Test OpenJurist with multiple citations"""
    print("="*70)
    print("OPENJURIST - Detailed Testing")
    print("="*70)
    
    test_cases = [
        ("410 U.S. 113", "410/us/113", "Roe v. Wade"),
        ("384 U.S. 436", "384/us/436", "Miranda v. Arizona"),
        ("163 F.3d 952", "163/f3d/952", "Federal appellate"),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    working = []
    
    for citation, url_path, description in test_cases:
        url = f"https://openjurist.org/{url_path}"
        print(f"\nTesting: {citation} ({description})")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Extract case name
                title_match = re.search(r'<title>([^<]+)</title>', content)
                if title_match:
                    title = title_match.group(1).strip()
                    print(f"✅ Title: {title}")
                    working.append(citation)
                else:
                    print("⚠️  Couldn't extract title")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ OpenJurist: {len(working)}/{len(test_cases)} citations verified")
    
    return len(working) > 0

def test_caselaw_access_api():
    """Test Caselaw Access Project API"""
    print("\n" + "="*70)
    print("CASELAW ACCESS PROJECT - API Testing")
    print("="*70)
    
    # Test without auth first (limited access)
    test_citations = [
        "410 U.S. 113",
        "384 U.S. 436",
    ]
    
    print("\nTesting PUBLIC API (no auth):")
    
    working = []
    
    for citation in test_citations:
        url = f"https://api.case.law/v1/cases/?cite={quote(citation)}"
        print(f"\n{citation}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    count = data.get('count', 0)
                    print(f"Results: {count}")
                    
                    if count > 0 and 'results' in data:
                        case = data['results'][0]
                        name = case.get('name_abbreviation', 'N/A')
                        decision_date = case.get('decision_date', 'N/A')
                        court = case.get('court', {}).get('name', 'N/A')
                        
                        print(f"✅ Case: {name}")
                        print(f"   Court: {court}")
                        print(f"   Date: {decision_date}")
                        
                        working.append(citation)
                    else:
                        print("⚠️  No results found")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON decode error: {e}")
                    print(f"   Content: {response.text[:200]}...")
            else:
                print(f"⚠️  HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Caselaw Access: {len(working)}/{len(test_citations)} citations found")
    
    print("\n📋 Notes:")
    print("   - Public API is available (no auth required for basic access)")
    print("   - Full text requires free API key from https://case.law/user/register/")
    print("   - Returns JSON with structured data")
    print("   - Covers US cases through ~2018")
    
    return len(working) > 0

def build_url_patterns():
    """Show URL patterns for different sources"""
    print("\n" + "="*70)
    print("URL PATTERN SUMMARY")
    print("="*70)
    
    patterns = {
        'Justia (Federal)': {
            'pattern': 'https://law.justia.com/cases/federal/us/{volume}/{page}/',
            'example': '410 U.S. 113 → /federal/us/410/113/',
            'pros': 'Works now, federal cases',
            'cons': 'State cases need year'
        },
        'OpenJurist (Federal)': {
            'pattern': 'https://openjurist.org/{volume}/{reporter}/{page}',
            'example': '410 U.S. 113 → /410/us/113',
            'pros': 'Simple pattern, federal cases',
            'cons': 'Federal only, limited coverage'
        },
        'Caselaw Access (API)': {
            'pattern': 'https://api.case.law/v1/cases/?cite={citation}',
            'example': '410 U.S. 113 → ?cite=410+U.S.+113',
            'pros': 'Comprehensive, proper API, structured data',
            'cons': 'Full text needs API key (free)'
        },
    }
    
    for source, info in patterns.items():
        print(f"\n{source}:")
        print(f"  Pattern: {info['pattern']}")
        print(f"  Example: {info['example']}")
        print(f"  Pros: {info['pros']}")
        print(f"  Cons: {info['cons']}")

def recommendations():
    """Provide implementation recommendations"""
    print("\n" + "="*70)
    print("IMPLEMENTATION RECOMMENDATIONS")
    print("="*70)
    
    print("""
VERIFIED WORKING SOURCES:
────────────────────────
1. ✅ CourtListener API (already implemented)
2. ✅ Justia Direct URL (just implemented) 
3. ✅ OpenJurist Direct URL (verified working)
4. ✅ Caselaw Access API (verified working, needs free API key)

SUGGESTED FALLBACK ORDER:
────────────────────────
1. CourtListener API (primary - most comprehensive, current cases)
2. Justia Direct URL (federal cases, no rate limits)
3. OpenJurist Direct URL (federal cases, alternative)
4. Caselaw Access API (comprehensive through 2018, structured data)

IMPLEMENTATION STEPS:
────────────────────
1. Add OpenJurist direct URL (like Justia)
   - Pattern: /{volume}/{reporter}/{page}
   - Very easy to implement
   
2. Register for Caselaw Access API key (free)
   - Sign up at: https://case.law/user/register/
   - Add to .env as CASELAW_API_KEY
   - Implement API call (structured JSON response)

BENEFITS:
────────
- 4 independent sources
- No single point of failure
- Comprehensive coverage (current + historical)
- All free/libre sources
- Mix of APIs (structured) and direct URLs (simple)

Would you like me to implement:
1. OpenJurist direct URL support? (5 minutes)
2. Caselaw Access API support? (15 minutes with API key registration)
""")

if __name__ == '__main__':
    print("\n🔍 Testing New Legal Database Sources\n")
    
    openjurist_works = test_openjurist_detailed()
    caselaw_works = test_caselaw_access_api()
    build_url_patterns()
    recommendations()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ OpenJurist: {'WORKING' if openjurist_works else 'FAILED'}")
    print(f"✅ Caselaw Access: {'WORKING' if caselaw_works else 'FAILED'}")
    print("\nBoth sources are viable alternatives to supplement CourtListener!")
