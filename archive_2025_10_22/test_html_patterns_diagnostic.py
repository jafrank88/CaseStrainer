"""
Diagnostic test to check if Bing/DuckDuckGo HTML patterns are broken
Saves actual HTML responses to see what structure they have
"""

import sys
sys.path.insert(0, '/app')

import requests
import re
from urllib.parse import quote

def test_bing_html():
    print("\n" + "="*80)
    print("BING HTML PATTERN DIAGNOSTIC")
    print("="*80)
    
    search_query = "17 F.4th 901"
    legal_query = f"{search_query} (site:leagle.com OR site:caselaw.findlaw.com)"
    search_url = f"https://www.bing.com/search?q={quote(legal_query)}"
    
    print(f"\nSearch URL: {search_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        if response.status_code == 200:
            html = response.text
            
            # Test OLD pattern
            old_pattern = r'<a[^>]*href="(https://[^"]*(?:leagle|findlaw|casetext)[^"]*)"[^>]*>([^<]*)</a>'
            old_matches = re.findall(old_pattern, html, re.IGNORECASE)
            print(f"\n❌ OLD PATTERN: Found {len(old_matches)} matches")
            
            # Try to find ANY links to legal sites
            all_links = re.findall(r'href="(https://[^"]*)"', html)
            legal_links = [link for link in all_links if any(site in link.lower() for site in ['leagle', 'findlaw', 'casetext', 'justia'])]
            print(f"✅ SIMPLE SEARCH: Found {len(legal_links)} legal site links")
            
            if legal_links:
                print(f"\nFirst 3 legal links found:")
                for link in legal_links[:3]:
                    print(f"  - {link}")
            
            # Save sample HTML for inspection
            with open('/app/bing_sample.html', 'w', encoding='utf-8') as f:
                f.write(html[:50000])  # First 50KB
            print(f"\n📄 Saved sample HTML to /app/bing_sample.html")
            
            # Look for specific HTML patterns in results
            print(f"\n🔍 Searching for common result containers...")
            patterns_to_test = [
                (r'<li class="b_algo', 'Bing result container (b_algo)'),
                (r'<cite>', 'Citation tags'),
                (r'<h2[^>]*>', 'H2 headers (result titles)'),
                (r'data-url=', 'Data URL attributes'),
                (r'class="b_attribution', 'Attribution class'),
            ]
            
            for pattern, description in patterns_to_test:
                count = len(re.findall(pattern, html, re.IGNORECASE))
                print(f"  - {description}: {count} found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_duckduckgo_html():
    print("\n" + "="*80)
    print("DUCKDUCKGO HTML PATTERN DIAGNOSTIC")
    print("="*80)
    
    search_query = "17 F.4th 901 case law"
    search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
    
    print(f"\nSearch URL: {search_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        if response.status_code == 200:
            html = response.text
            
            # Test OLD pattern
            old_pattern = r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            old_matches = re.findall(old_pattern, html, re.IGNORECASE)
            print(f"\n❌ OLD PATTERN: Found {len(old_matches)} matches")
            
            # Try to find ANY result links
            all_links = re.findall(r'href="([^"]*)"', html)
            legal_links = [link for link in all_links if any(site in link.lower() for site in ['leagle', 'findlaw', 'casetext', 'justia'])]
            print(f"✅ SIMPLE SEARCH: Found {len(legal_links)} legal site links")
            
            if legal_links:
                print(f"\nFirst 3 legal links found:")
                for link in legal_links[:3]:
                    print(f"  - {link}")
            
            # Save sample HTML for inspection
            with open('/app/ddg_sample.html', 'w', encoding='utf-8') as f:
                f.write(html[:50000])  # First 50KB
            print(f"\n📄 Saved sample HTML to /app/ddg_sample.html")
            
            # Look for specific HTML patterns in results
            print(f"\n🔍 Searching for common result containers...")
            patterns_to_test = [
                (r'class="result', 'Result class'),
                (r'class="result__', 'Result__ prefix classes'),
                (r'data-testid="result', 'Result test ID'),
                (r'<div[^>]*class="[^"]*snippet[^"]*"', 'Snippet divs'),
                (r'<a[^>]*class="[^"]*result', 'Result links'),
            ]
            
            for pattern, description in patterns_to_test:
                count = len(re.findall(pattern, html, re.IGNORECASE))
                print(f"  - {description}: {count} found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bing_html()
    test_duckduckgo_html()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nIf the OLD PATTERN shows 0 matches but SIMPLE SEARCH finds links,")
    print("then the regex patterns are MISCONFIGURED and need updating.")
    print("\nCheck the saved HTML files to see the actual structure:")
    print("  - /app/bing_sample.html")
    print("  - /app/ddg_sample.html")
    print("="*80)
