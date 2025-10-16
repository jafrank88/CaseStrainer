#!/usr/bin/env python
"""Diagnose why fallback sources aren't working"""

import requests
from urllib.parse import quote
import re

def test_justia():
    """Test Justia search directly"""
    citation = "384 U.S. 436"
    case_name = "Miranda v. Arizona"
    
    search_query = f"{citation} {case_name}"
    search_url = f"https://law.justia.com/search?query={quote(search_query)}"
    
    print("="*70)
    print("TESTING JUSTIA")
    print("="*70)
    print(f"URL: {search_url}\n")
    
    try:
        response = requests.get(search_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        # Look for the pattern used in the code
        case_link_pattern = r'<a[^>]*href="([^"]*cases[^"]+)"[^>]*>([^<]*)</a>'
        matches = re.findall(case_link_pattern, response.text, re.IGNORECASE)
        
        print(f"Matches found: {len(matches)}")
        
        if matches:
            print("\nFirst 5 matches:")
            for i, (url, text) in enumerate(matches[:5], 1):
                print(f"{i}. URL: {url[:80]}...")
                print(f"   Text: {text[:80]}...")
        else:
            # Try to find any links
            any_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]{10,})</a>', response.text[:5000])
            print(f"\nAny links in first 5KB: {len(any_links)}")
            if any_links:
                print("Sample links:")
                for url, text in any_links[:3]:
                    print(f"  - {text[:50]}...")
            
            # Check for common anti-bot indicators
            if 'captcha' in response.text.lower():
                print("\n⚠️  CAPTCHA detected!")
            if 'robot' in response.text.lower() or 'bot' in response.text.lower():
                print("\n⚠️  Bot detection possible")
            if response.status_code == 403:
                print("\n⚠️  403 Forbidden - likely blocking automated access")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_google_scholar():
    """Test Google Scholar directly"""
    citation = "384 U.S. 436"
    case_name = "Miranda v. Arizona"
    
    search_query = f'"{citation}" "{case_name}"'
    search_url = f"https://scholar.google.com/scholar?hl=en&q={quote(search_query)}"
    
    print("\n" + "="*70)
    print("TESTING GOOGLE SCHOLAR")
    print("="*70)
    print(f"URL: {search_url}\n")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        # Look for the pattern
        title_pattern = r'<h3[^>]*class="gs_rt"[^>]*>(?:<a[^>]*>)?([^<]+)</h3>'
        titles = re.findall(title_pattern, response.text, re.IGNORECASE)
        
        print(f"Titles found: {len(titles)}")
        
        if titles:
            print("\nTitles:")
            for i, title in enumerate(titles[:5], 1):
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                print(f"{i}. {clean_title[:80]}...")
        else:
            # Check what we got
            h3_tags = re.findall(r'<h3[^>]*>([^<]*)</h3>', response.text[:5000])
            print(f"\nAny h3 tags in first 5KB: {len(h3_tags)}")
            
            # Check for anti-bot
            if 'captcha' in response.text.lower():
                print("\n⚠️  CAPTCHA detected!")
            if 'unusual traffic' in response.text.lower():
                print("\n⚠️  'Unusual traffic' message detected - Google is blocking bots")
            if response.status_code == 403:
                print("\n⚠️  403 Forbidden")
            if response.status_code == 429:
                print("\n⚠️  429 Too Many Requests - rate limited")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_findlaw():
    """Test FindLaw directly"""
    citation = "384 U.S. 436"
    case_name = "Miranda v. Arizona"
    
    search_query = f"{citation} {case_name}"
    search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
    
    print("\n" + "="*70)
    print("TESTING FINDLAW")
    print("="*70)
    print(f"URL: {search_url}\n")
    
    try:
        response = requests.get(search_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        # Look for pattern
        case_link_pattern = r'<a[^>]*href="([^"]*court[^"]+)"[^>]*>([^<]*)</a>'
        matches = re.findall(case_link_pattern, response.text, re.IGNORECASE)
        
        print(f"Matches found: {len(matches)}")
        
        if matches:
            print("\nFirst 5 matches:")
            for i, (url, text) in enumerate(matches[:5], 1):
                print(f"{i}. {text[:60]}...")
        else:
            # Check for any links
            any_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]{10,})</a>', response.text[:5000])
            print(f"\nAny links in first 5KB: {len(any_links)}")
            
            # Check for anti-bot
            if 'captcha' in response.text.lower():
                print("\n⚠️  CAPTCHA detected!")
            if response.status_code == 403:
                print("\n⚠️  403 Forbidden")
            if 'robot' in response.text.lower():
                print("\n⚠️  Robot detection possible")
                
            # Save response for inspection
            with open('findlaw_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:10000])
            print("\n💾 Saved first 10KB to findlaw_response.html for inspection")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def summary():
    """Print summary"""
    print("\n" + "="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)
    print("""
Common reasons fallback sources fail:

1. **Anti-Bot Protection**
   - Sites detect automated requests and block them
   - CAPTCHA challenges
   - 403 Forbidden responses
   - "Unusual traffic" messages

2. **HTML Structure Changes**
   - Sites redesign their HTML
   - CSS classes change
   - Link patterns change
   - Our regex patterns become outdated

3. **Rate Limiting**
   - Too many requests in short time
   - 429 Too Many Requests
   - Temporary IP bans

4. **User-Agent Required**
   - Sites require proper browser User-Agent
   - May need cookies/JavaScript

5. **Search Query Format**
   - Our query format doesn't match site's expectations
   - Need different encoding or parameters

RECOMMENDATION:
- CourtListener is a proper API with authentication
- Other sources are web scrapers and inherently unreliable
- Consider them "nice to have" not "need to have"
- Focus on keeping CourtListener working (which it is!)
""")

if __name__ == '__main__':
    print("\n🔍 Diagnosing Fallback Verification Sources\n")
    
    test_justia()
    test_google_scholar()
    test_findlaw()
    summary()
