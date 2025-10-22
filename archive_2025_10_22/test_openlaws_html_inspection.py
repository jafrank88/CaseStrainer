"""
Inspect OpenLaws HTML structure to see if link patterns are correct
"""

import requests
import re
from urllib.parse import quote

def inspect_openlaws():
    print("\n" + "="*80)
    print("OPENLAWS HTML STRUCTURE INSPECTION")
    print("="*80)
    
    # Test citation
    search_query = "436 U.S. 49"
    search_url = f"https://openlaws.com/search?query={quote(search_query)}"
    
    print(f"\nSearch URL: {search_url}")
    print(f"Citation: {search_query}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        if response.status_code == 200:
            html = response.text
            
            # Save first 100KB for inspection
            with open('/tmp/openlaws_search_sample.html', 'w', encoding='utf-8') as f:
                f.write(html[:100000])
            print(f"\n📄 Saved sample HTML to /tmp/openlaws_search_sample.html")
            
            # Check for common indicators
            print(f"\n🔍 Content Analysis:")
            print(f"  - Contains 'case': {html.lower().count('case')}")
            print(f"  - Contains 'decision': {html.lower().count('decision')}")
            print(f"  - Contains citation text: {html.lower().count(search_query.lower())}")
            
            # Test current patterns
            print(f"\n❌ CURRENT PATTERNS:")
            patterns_to_test = [
                (r'href="(/case/[^"]+)"', '/case/ pattern'),
                (r'href="(/decision/[^"]+)"', '/decision/ pattern'),
                (r'href="(https://openlaws\.com/case/[^"]+)"', 'https://openlaws.com/case/ pattern'),
                (r'href="(https://openlaws\.com/decision/[^"]+)"', 'https://openlaws.com/decision/ pattern'),
            ]
            
            total_matches = 0
            for pattern, description in patterns_to_test:
                matches = re.findall(pattern, html, re.IGNORECASE)
                print(f"  - {description}: {len(matches)} matches")
                total_matches += len(matches)
            
            print(f"\n  Total: {total_matches} matches")
            
            # Look for ANY links
            print(f"\n✅ EXPLORATORY PATTERNS:")
            exploratory_patterns = [
                (r'href="([^"]*case[^"]*)"', 'Any href with "case"'),
                (r'href="([^"]*decision[^"]*)"', 'Any href with "decision"'),
                (r'href="([^"]*openlaws[^"]*)"', 'Any href with "openlaws"'),
                (r'href="(/[^"]+)"', 'Any relative links'),
                (r'<a[^>]*href="([^"]+)"', 'All links'),
            ]
            
            for pattern, description in exploratory_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                print(f"  - {description}: {len(matches)} matches")
                if len(matches) > 0 and len(matches) < 20:
                    print(f"    First 3: {matches[:3]}")
            
            # Check if it's JavaScript-rendered
            print(f"\n🔬 JavaScript Detection:")
            js_indicators = [
                ('React', html.count('react')),
                ('Vue', html.count('vue')),
                ('Angular', html.count('angular')),
                ('<script', html.count('<script')),
                ('window.__INITIAL_STATE__', html.count('window.__INITIAL_STATE__')),
                ('data-react', html.count('data-react')),
            ]
            
            for indicator, count in js_indicators:
                if count > 0:
                    print(f"  - {indicator}: {count} occurrences")
            
            # Check for "no results" indicators
            print(f"\n⚠️  No Results Indicators:")
            no_results_indicators = [
                'no results',
                'no cases found',
                'no matches',
                '0 results',
                'try again',
                'did not match',
            ]
            
            for indicator in no_results_indicators:
                if indicator in html.lower():
                    print(f"  - Found: '{indicator}'")
            
            # Look for actual case titles in the HTML
            print(f"\n📋 Potential Case Titles (v. pattern):")
            title_matches = re.findall(r'>([^<]*\sv\.\s[^<]{10,60})</i', html, re.IGNORECASE)
            if title_matches:
                for i, title in enumerate(title_matches[:5]):
                    print(f"  {i+1}. {title.strip()}")
            else:
                print(f"  No case titles found with ' v. ' pattern")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    print("\nIf current patterns show 0 matches but exploratory patterns find links,")
    print("then the patterns need updating.")
    print("\nIf JavaScript indicators are high, the site may require JavaScript rendering")
    print("(would need Playwright or Selenium).")
    print("\nIf 'no results' indicators are found, the search itself is failing.")
    print("="*80)

if __name__ == '__main__':
    inspect_openlaws()
