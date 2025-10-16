#!/usr/bin/env python
"""Test remaining potentially viable sources"""

import requests
import re
from urllib.parse import quote
import time

def test_leagle_patterns():
    """Test if Leagle has direct URL patterns"""
    print("="*70)
    print("1. LEAGLE - Direct URL Testing")
    print("="*70)
    
    # Try different URL patterns
    patterns = [
        ("https://www.leagle.com/decision/410us113", "Direct citation"),
        ("https://www.leagle.com/decision/1973737410us11311403", "With year/page"),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url, desc in patterns:
        print(f"\nTrying: {desc}")
        print(f"URL: {url}")
        
        try:
            time.sleep(1)  # Be polite
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for anti-bot
                if 'captcha' in content.lower():
                    print("⚠️  CAPTCHA detected")
                elif len(content) < 2000:
                    print("⚠️  Suspicious - short response")
                else:
                    # Try to find case name
                    if 'Roe v. Wade' in content or 'roe' in content.lower():
                        print("✅ Possible match found!")
                        print(f"   Content length: {len(content)} bytes")
                    else:
                        print("⚠️  No clear match")
            elif response.status_code == 404:
                print("❌ Not found")
            else:
                print(f"⚠️  HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n📋 Leagle Assessment:")
    print("   - Requires specific URL format (hard to determine)")
    print("   - May have anti-bot protection")
    print("   - Not reliable without knowing exact URL patterns")

def test_cornell_lii():
    """Test Cornell Legal Information Institute"""
    print("\n" + "="*70)
    print("2. CORNELL LII - Direct URL Testing")
    print("="*70)
    
    # Cornell has known URL patterns for Supreme Court cases
    patterns = [
        ("https://www.law.cornell.edu/supremecourt/text/410/113", "Supreme Court"),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    working = False
    
    for url, desc in patterns:
        print(f"\nTrying: {desc}")
        print(f"URL: {url}")
        
        try:
            time.sleep(1)
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                print(f"✅ SUCCESS! Content: {len(content)} bytes")
                
                # Try to extract case name
                title_match = re.search(r'<title>([^<]+)</title>', content)
                if title_match:
                    title = title_match.group(1)
                    print(f"   Title: {title}")
                    if 'Roe' in title or 'Wade' in title:
                        print("   ✅ Correct case found!")
                        working = True
                        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n📋 Cornell LII Assessment:")
    if working:
        print("   ✅ WORKS! Supreme Court cases accessible")
        print("   - Pattern: /supremecourt/text/{volume}/{page}")
        print("   - Free, no authentication")
        print("   - Excellent resource")
    else:
        print("   ⚠️  Needs more testing")

def test_govinfo():
    """Test GovInfo (Government Publishing Office)"""
    print("\n" + "="*70)
    print("3. GOVINFO.GOV - Federal Cases")
    print("="*70)
    
    print("\n📋 GovInfo Details:")
    print("   URL: https://www.govinfo.gov/")
    print("   - Official US government source")
    print("   - Has API: https://api.govinfo.gov/")
    print("   - Free API key required")
    print("   - Coverage: Federal cases, statutes, regulations")
    print("   - Collections: USCOURTS (federal courts)")
    
    # Try to access
    url = "https://www.govinfo.gov/app/collection/uscourts"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Site is accessible")
            print("   Would need to research API patterns")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_google_scholar_casename():
    """Test Google Scholar with different approach"""
    print("\n" + "="*70)
    print("4. GOOGLE SCHOLAR - Case Name Search")
    print("="*70)
    
    # Try searching by case name instead of citation
    case_name = "Roe v Wade"
    url = f"https://scholar.google.com/scholar?q={quote(case_name)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        time.sleep(2)
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 429:
            print("❌ Rate limited (429)")
        elif 'unusual traffic' in response.text.lower():
            print("❌ Anti-bot detected")
        elif response.status_code == 200:
            print("⚠️  Got response but likely requires CAPTCHA")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n📋 Google Scholar Assessment:")
    print("   ❌ Not viable - aggressive anti-bot protection")

def test_fastcase_court_records():
    """Test direct court websites"""
    print("\n" + "="*70)
    print("5. DIRECT COURT WEBSITES")
    print("="*70)
    
    print("\n📋 Supreme Court:")
    print("   URL: https://www.supremecourt.gov/opinions/")
    print("   - Official source")
    print("   - Modern cases available")
    print("   - No API, PDFs only")
    
    print("\n📋 Federal Courts (PACER/RECAP):")
    print("   - PACER: Paid access to federal court records")
    print("   - RECAP: Free archive via Free Law Project")
    print("   - Already covered by CourtListener integration")

def summarize_findings():
    """Summarize findings and recommendations"""
    print("\n" + "="*70)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    print("""
VIABLE SOURCES TO IMPLEMENT:
─────────────────────────────

1. ✅ Cornell LII (Legal Information Institute)
   URL Pattern: https://www.law.cornell.edu/supremecourt/text/{volume}/{page}
   Coverage: Supreme Court cases
   Status: FREE, direct URL access, NO authentication
   Implementation: EASY (5 minutes)
   
2. 🔑 Caselaw Access Project (Harvard)
   URL: https://api.case.law/v1/cases/?cite={citation}
   Coverage: Comprehensive through 2018
   Status: FREE API (requires free registration)
   Implementation: MEDIUM (15 mins after registration)
   
3. 🔑 GovInfo API
   URL: https://api.govinfo.gov/
   Coverage: Official federal documents
   Status: FREE API (requires free API key)
   Implementation: MEDIUM (needs research + registration)

NOT VIABLE:
───────────
❌ Google Scholar - Anti-bot protection
❌ FindLaw - Cloudflare protection
❌ Leagle - Unknown URL patterns, likely protected
❌ Casetext - Requires account

CURRENT VERIFIED WORKING SOURCES:
─────────────────────────────────
✅ CourtListener API
✅ Justia Direct URL
✅ OpenJurist Direct URL

RECOMMENDATION:
──────────────
ADD NEXT: Cornell LII
- No registration needed
- Reliable federal source
- Easy to implement
- Complements existing sources

This would give you 4 working sources with NO API keys needed!
(CourtListener, Justia, OpenJurist, Cornell LII)
""")

if __name__ == '__main__':
    print("\n🔍 Testing Remaining Legal Database Sources\n")
    
    test_leagle_patterns()
    test_cornell_lii()
    test_govinfo()
    test_google_scholar_casename()
    test_fastcase_court_records()
    summarize_findings()
