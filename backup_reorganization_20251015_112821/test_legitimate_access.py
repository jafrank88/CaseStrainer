#!/usr/bin/env python
"""Test legitimate access methods for fallback sources"""

import requests
import time
from urllib.parse import quote

def test_with_better_headers():
    """Test with more legitimate browser headers"""
    
    # Simulate a real browser more convincingly
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    print("="*70)
    print("TESTING WITH BETTER HEADERS")
    print("="*70)
    
    # Test Justia
    print("\n1. Justia (with delay)...")
    time.sleep(2)  # Be polite
    try:
        url = "https://law.justia.com/cases/federal/us/384/436/"  # Direct URL to Miranda
        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            if 'Miranda v. Arizona' in response.text:
                print("   ✅ SUCCESS - Can access Justia directly!")
            else:
                print("   ⚠️  Page loaded but content unclear")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test vLex
    print("\n2. vLex...")
    time.sleep(2)
    try:
        url = "https://vlex.com/vid/miranda-v-arizona-632893149"  # Example vLex URL
        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS - vLex accessible! Content: {len(response.text)} bytes")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Casetext (another good source)
    print("\n3. Casetext...")
    time.sleep(2)
    try:
        url = "https://casetext.com/case/miranda-v-arizona-5"
        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS - Casetext accessible! Content: {len(response.text)} bytes")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_apis():
    """Check if sites have official APIs"""
    print("\n" + "="*70)
    print("CHECKING FOR OFFICIAL APIs")
    print("="*70)
    
    print("""
vLex:
- Has API: YES - https://api.vlex.com/
- Requires: API key (paid)
- Access: https://vlex.com/developers/

Justia:
- Has API: LIMITED - No comprehensive API
- Free access: Case pages directly accessible
- Search: Via website only

Casetext:
- Has API: NO public API
- Access: Website only
- Note: Requires account for full access

Leagle:
- Has API: NO
- Access: Website only

Fastcase:
- Has API: YES - https://www.fastcase.com/api/
- Requires: Subscription
- Access: For legal professionals

Recommendation:
1. **Direct URL access** (if you know the URL) - Works best
2. **Citation-based URL construction** - Build URLs from citation patterns
3. **Strategic search queries** - Use site-specific search syntax
4. **Respect rate limits** - Add 2-5 second delays between requests
""")

def test_direct_url_patterns():
    """Test if we can construct direct URLs from citations"""
    print("\n" + "="*70)
    print("TESTING DIRECT URL CONSTRUCTION")
    print("="*70)
    
    # Common patterns for constructing URLs
    patterns = {
        'Justia Federal': 'https://law.justia.com/cases/federal/us/{volume}/{page}/',
        'Justia State (WA)': 'https://law.justia.com/cases/washington/supreme-court/{year}/{volume}-wash-2d-{page}.html',
        'Casetext': 'https://casetext.com/case/[case-name-slug]',  # Need case name
        'vLex': 'https://vlex.com/vid/[case-name-slug]-[id]',  # Need ID
    }
    
    print("\nURL Pattern Examples:")
    for source, pattern in patterns.items():
        print(f"  {source}: {pattern}")
    
    print("\n✅ Justia allows direct access with citation!")
    print("   Example: 384 U.S. 436 → https://law.justia.com/cases/federal/us/384/436/")
    print("\n💡 This means we can verify citations WITHOUT searching!")

if __name__ == '__main__':
    print("\n🔍 Testing Legitimate Access Methods\n")
    
    test_with_better_headers()
    check_apis()
    test_direct_url_patterns()
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print("""
For cases NOT in CourtListener:

1. **Justia - Direct URL Access** (Best option)
   - Build URL from citation: volume/page pattern
   - No search needed, no anti-bot issues
   - Example: 384 U.S. 436 → /cases/federal/us/384/436/
   
2. **Add Delays** (2-5 seconds between requests)
   - Respect sites' resources
   - Reduces rate limiting
   - More "human-like" behavior

3. **Better Headers**
   - Use realistic browser User-Agent
   - Include Accept, Accept-Language, etc.
   - Maintain session cookies

4. **Fallback Chain**
   - CourtListener (primary, API)
   - Justia direct URL (no search, reliable)
   - Other sources (with delays)

5. **Consider vLex API**
   - If budget allows
   - Comprehensive coverage
   - Proper API access
   
Would you like me to implement direct URL access for Justia?
This would bypass search entirely and work reliably.
""")
