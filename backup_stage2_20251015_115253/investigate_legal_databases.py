#!/usr/bin/env python
"""Investigate reliable access methods for legal databases"""

import requests
import re
from urllib.parse import quote
import time

def test_caselaw_access():
    """Test Caselaw Access Project (Harvard)"""
    print("="*70)
    print("1. CASELAW ACCESS PROJECT (Harvard)")
    print("="*70)
    print("URL: https://case.law/")
    print("Type: FREE API with authentication")
    print("Coverage: Comprehensive US case law\n")
    
    # Test if API is accessible
    try:
        # Public API endpoint
        url = "https://api.case.law/v1/cases/?cite=410 U.S. 113"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is accessible!")
            print(f"   Results: {data.get('count', 0)} cases found")
            if data.get('results'):
                case = data['results'][0]
                print(f"   Case: {case.get('name_abbreviation', 'N/A')}")
                print(f"   Citations: {case.get('citations', [])}")
        else:
            print(f"⚠️  Status {response.status_code}")
            
        print("\n📋 Details:")
        print("   - Requires free API key from https://case.law/api/")
        print("   - Bulk data access available")
        print("   - 480+ volumes, 40M pages")
        print("   - All state & federal cases through ~2018")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_openjurist():
    """Test OpenJurist"""
    print("\n" + "="*70)
    print("2. OPENJURIST")
    print("="*70)
    print("URL: https://openjurist.org/")
    print("Type: Free access, no API")
    print("Coverage: Federal cases\n")
    
    try:
        # Try direct URL pattern
        url = "https://openjurist.org/410/us/113"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Direct URL test: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Direct URL access works!")
            print(f"   Content: {len(response.text)} bytes")
            
            # Check for case name
            if 'Roe v. Wade' in response.text:
                print(f"   ✅ Case found!")
        else:
            print(f"⚠️  Direct URL returned {response.status_code}")
            
        print("\n📋 Details:")
        print("   - Supports direct URL: /volume/reporter/page")
        print("   - Example: /410/us/113 for 410 U.S. 113")
        print("   - Free, no authentication")
        print("   - Federal cases only")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_leagle():
    """Test Leagle"""
    print("\n" + "="*70)
    print("3. LEAGLE")
    print("="*70)
    print("URL: https://leagle.com/")
    print("Type: Free access, no API")
    print("Coverage: State & federal\n")
    
    try:
        # Test search
        search_query = "410 U.S. 113"
        url = f"https://www.leagle.com/decision/{quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Search test: {response.status_code}")
        print(f"Content: {len(response.text)} bytes")
        
        if response.status_code == 200:
            # Check for anti-bot
            if 'captcha' in response.text.lower():
                print("⚠️  CAPTCHA detected")
            elif len(response.text) < 1000:
                print("⚠️  Suspicious - very short response")
            else:
                print("✅ May be accessible")
                
        print("\n📋 Details:")
        print("   - Search-based access")
        print("   - May have anti-bot protection")
        print("   - Free but no API")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_courtlistener_bulk():
    """Test CourtListener bulk access"""
    print("\n" + "="*70)
    print("4. COURTLISTENER - BULK DATA")
    print("="*70)
    print("URL: https://www.courtlistener.com/")
    print("Type: API + Bulk downloads\n")
    
    print("📋 Additional Features:")
    print("   - Bulk data downloads available")
    print("   - PostgreSQL database dumps")
    print("   - Citation network data")
    print("   - RECAP (PACER archive)")
    print("   - Opinion clusters with parallel citations")
    print("   - Free with API key (we already have)")

def test_vlex_api():
    """Test vLex API"""
    print("\n" + "="*70)
    print("5. VLEX")
    print("="*70)
    print("URL: https://vlex.com/")
    print("Type: Commercial API\n")
    
    print("📋 Details:")
    print("   - Comprehensive international coverage")
    print("   - Professional API with authentication")
    print("   - Requires paid subscription")
    print("   - API docs: https://vlex.com/developers/")
    print("   - Would need to evaluate cost/benefit")

def test_free_law_project():
    """Test Free Law Project resources"""
    print("\n" + "="*70)
    print("6. FREE LAW PROJECT ECOSYSTEM")
    print("="*70)
    print("URL: https://free.law/")
    print("Type: Multiple free resources\n")
    
    print("📋 Projects:")
    print("   1. CourtListener (we use this)")
    print("   2. RECAP - PACER documents")
    print("   3. Judge database")
    print("   4. Judicial financial disclosures")
    print("   5. Oral argument audio")
    print("   All with APIs and bulk data access")

def test_state_specific():
    """Test state-specific resources"""
    print("\n" + "="*70)
    print("7. STATE-SPECIFIC RESOURCES")
    print("="*70)
    
    print("\n📋 Washington State Courts:")
    print("   URL: https://www.courts.wa.gov/opinions/")
    print("   - Official source for WA cases")
    print("   - Free access, no API")
    print("   - Recent opinions available as PDFs")
    
    print("\n📋 California Courts:")
    print("   URL: https://www.courts.ca.gov/opinions.htm")
    print("   - Official source for CA cases")
    print("   - Free access, no API")

def summarize_recommendations():
    """Provide recommendations"""
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    print("""
TIER 1 - IMPLEMENT NOW (Free & Reliable):
─────────────────────────────────────────
1. ✅ CourtListener API (already implemented)
2. ✅ Justia Direct URL (just implemented)
3. 🆕 Caselaw Access Project API
   - Register at: https://case.law/api/
   - Free API key
   - Comprehensive coverage through 2018
   - Direct citation lookup
   - Pattern: /v1/cases/?cite=410+U.S.+113

4. 🆕 OpenJurist Direct URL
   - Pattern: https://openjurist.org/{volume}/{reporter}/{page}
   - Example: /410/us/113
   - No authentication needed
   - Federal cases only

TIER 2 - CONSIDER (Require Work):
──────────────────────────────────
5. State Court Official Sites
   - For state-specific cases
   - May need custom scrapers per state
   - Official sources = authoritative

TIER 3 - EVALUATE (Paid):
─────────────────────────
6. vLex API
   - Comprehensive but paid
   - Evaluate if budget allows

IMPLEMENTATION PRIORITY:
────────────────────────
1. Caselaw Access Project (Harvard) - FREE API, huge coverage
2. OpenJurist - Direct URL like Justia, easy to implement
3. State-specific for edge cases

With these additions, you'd have:
- CourtListener (API, primary)
- Justia (direct URL, federal)
- Caselaw Access (API, comprehensive through 2018)
- OpenJurist (direct URL, federal)
- State courts (as needed)

This would cover nearly all citations reliably!
""")

if __name__ == '__main__':
    print("\n🔍 Investigating Reliable Legal Database Access Methods\n")
    
    test_caselaw_access()
    test_openjurist()
    test_leagle()
    test_courtlistener_bulk()
    test_vlex_api()
    test_free_law_project()
    test_state_specific()
    summarize_recommendations()
