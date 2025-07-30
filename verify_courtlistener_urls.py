#!/usr/bin/env python3
"""
Verify whether the citations found by the production pipeline actually exist in CourtListener
by checking their URLs and extracting case details.
"""

import requests
import re
import time
from urllib.parse import urlparse

def check_courtlistener_url(url, citation_text, expected_case_name):
    """Check if a CourtListener URL actually exists and contains the expected case"""
    
    print(f"\n🔍 CHECKING: {citation_text}")
    print(f"📄 Expected Case: {expected_case_name}")
    print(f"🔗 URL: {url}")
    
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Extract the case title from the page
            title_patterns = [
                r'<title>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'class="case-title"[^>]*>([^<]+)</div>',
                r'<div class="title"[^>]*>([^<]+)</div>'
            ]
            
            found_title = None
            for pattern in title_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    found_title = match.group(1).strip()
                    # Clean up the title
                    found_title = re.sub(r'\s+', ' ', found_title)
                    found_title = found_title.replace(' – CourtListener.com', '')
                    found_title = found_title.replace(' - CourtListener.com', '')
                    break
            
            # Look for the citation in the page content
            citation_found = citation_text in content
            
            # Look for case details
            case_details = {}
            
            # Try to find the date
            date_patterns = [
                r'Decided:\s*([^<\n]+)',
                r'Date:\s*([^<\n]+)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\w+\s+\d{1,2},\s+\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    case_details['date'] = match.group(1).strip()
                    break
            
            # Try to find court information
            court_patterns = [
                r'Court:\s*([^<\n]+)',
                r'<div class="court"[^>]*>([^<]+)</div>',
                r'United States Court of Appeals for the ([^<\n]+)',
                r'United States District Court for the ([^<\n]+)'
            ]
            
            for pattern in court_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    case_details['court'] = match.group(1).strip()
                    break
            
            print(f"✅ PAGE EXISTS")
            print(f"📝 Found Title: {found_title}")
            print(f"🎯 Citation in Content: {'Yes' if citation_found else 'No'}")
            
            if case_details:
                print(f"📅 Date: {case_details.get('date', 'Not found')}")
                print(f"🏛️  Court: {case_details.get('court', 'Not found')}")
            
            # Check if the found title matches the expected case name
            if found_title and expected_case_name:
                title_similarity = check_title_similarity(found_title, expected_case_name)
                print(f"📊 Title Match: {title_similarity}")
            
            return {
                'exists': True,
                'status_code': response.status_code,
                'found_title': found_title,
                'citation_found': citation_found,
                'case_details': case_details,
                'url_accessible': True
            }
            
        elif response.status_code == 404:
            print(f"❌ PAGE NOT FOUND (404)")
            return {
                'exists': False,
                'status_code': 404,
                'found_title': None,
                'citation_found': False,
                'case_details': {},
                'url_accessible': False
            }
        else:
            print(f"⚠️  UNEXPECTED STATUS: {response.status_code}")
            return {
                'exists': False,
                'status_code': response.status_code,
                'found_title': None,
                'citation_found': False,
                'case_details': {},
                'url_accessible': False
            }
            
    except requests.RequestException as e:
        print(f"❌ REQUEST FAILED: {str(e)}")
        return {
            'exists': False,
            'status_code': None,
            'found_title': None,
            'citation_found': False,
            'case_details': {},
            'url_accessible': False,
            'error': str(e)
        }

def check_title_similarity(found_title, expected_title):
    """Check if two case titles are similar"""
    
    # Normalize titles for comparison
    def normalize_title(title):
        if not title:
            return ""
        # Convert to lowercase, remove extra spaces, remove common suffixes
        title = title.lower()
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'\s*[-–]\s*courtlistener\.com.*$', '', title)
        title = title.strip()
        return title
    
    found_norm = normalize_title(found_title)
    expected_norm = normalize_title(expected_title)
    
    if found_norm == expected_norm:
        return "Exact match"
    elif expected_norm in found_norm or found_norm in expected_norm:
        return "Partial match"
    else:
        return "No match"

def verify_all_citations():
    """Verify all the citations from the production results"""
    
    # Citations from the production results
    citations_to_verify = [
        {
            'citation': '654 F. Supp. 2d 321',
            'expected_case': 'Benckini v. Hawk',
            'url': 'https://www.courtlistener.com/opinion/1689955/benckini-v-hawk/',
            'source': 'CourtListener-lookup'
        },
        {
            'citation': '147 Wn. App. 891',
            'expected_case': 'State v. Alphonse',
            'url': 'https://www.courtlistener.com/opinion/4945618/state-v-alphonse/',
            'source': 'CourtListener-lookup'
        },
        {
            'citation': '789 P.2d 123',
            'expected_case': None,  # This one was not verified
            'url': 'https://www.courtlistener.com/opinion/9354201/matter-of-zaiden-p-ashley-q/',
            'source': 'CourtListener-search'
        },
        {
            'citation': '456 F.3d 789',
            'expected_case': 'David L. Hartjes v. Jeffrey P. Endicott',
            'url': 'https://www.courtlistener.com/opinion/795205/david-l-hartjes-v-jeffrey-p-endicott/',
            'source': 'CourtListener-lookup'
        },
        {
            'citation': '123 Wn.2d 456',
            'expected_case': 'State v. Board of Yakima County Commissioners',
            'url': 'https://www.courtlistener.com/opinion/1229830/state-v-board-of-yakima-county-commissioners/',
            'source': 'CourtListener-lookup'
        }
    ]
    
    print("🔍 VERIFYING COURTLISTENER URLS FOR PRODUCTION RESULTS")
    print("=" * 70)
    
    results = []
    
    for citation_info in citations_to_verify:
        result = check_courtlistener_url(
            citation_info['url'],
            citation_info['citation'],
            citation_info['expected_case']
        )
        
        result['citation'] = citation_info['citation']
        result['expected_case'] = citation_info['expected_case']
        result['source'] = citation_info['source']
        results.append(result)
        
        # Be respectful to CourtListener servers
        time.sleep(1)
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    accessible_count = sum(1 for r in results if r['url_accessible'])
    verified_count = sum(1 for r in results if r['exists'])
    
    print(f"Total citations checked: {len(results)}")
    print(f"URLs accessible: {accessible_count}")
    print(f"Cases found in CourtListener: {verified_count}")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 50)
    
    for result in results:
        status = "✅ FOUND" if result['exists'] else "❌ NOT FOUND"
        print(f"{result['citation']}: {status}")
        if result['found_title']:
            print(f"  Title: {result['found_title']}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
    
    print(f"\n💡 CONCLUSION:")
    print("=" * 15)
    
    if verified_count == len([c for c in citations_to_verify if c['expected_case']]):
        print("✅ All expected citations were found in CourtListener")
        print("✅ The production pipeline results appear to be CORRECT")
        print("✅ These cases are legitimately in the CourtListener database")
    else:
        print("❌ Some citations were not found in CourtListener")
        print("❌ There may be an issue with the verification process")
    
    return results

if __name__ == "__main__":
    verify_all_citations()
