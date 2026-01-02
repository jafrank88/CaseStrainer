#!/usr/bin/env python3
"""
Extract actual file links and find case closest to page 584
"""

import requests
import re

def find_case_by_file_links():
    """Find case by analyzing actual file links"""
    
    base_url = "https://law.resource.org/pub/us/case/reporter/F3/161/"
    target_page = 584
    
    print(f"🔍 Looking for case closest to page {target_page}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Extract all case links with their citations
            # Pattern: <a href="filename.html" title="Case Name">161 F.3d page</a>
            link_pattern = r'<a href="([^"]+)" title="([^"]*)"[^>]*>([^<]+)</a>'
            matches = re.findall(link_pattern, content)
            
            print(f"📊 Found {len(matches)} case links")
            
            case_list = []
            for filename, title, citation in matches:
                if 'F.3d' in citation:
                    # Extract page number from citation
                    page_match = re.search(r'F\.?3d\s+(\d+)', citation)
                    if page_match:
                        page = int(page_match.group(1))
                        case_list.append({
                            'filename': filename,
                            'title': title,
                            'citation': citation,
                            'page': page,
                            'diff': abs(page - target_page)
                        })
            
            # Sort by difference from target page
            case_list.sort(key=lambda x: x['diff'])
            
            print(f"\n📋 Cases closest to page {target_page}:")
            for i, case in enumerate(case_list[:10]):
                print(f"   {i+1}. {case['citation']} - page {case['page']} ({case['diff']} pages away)")
                print(f"      File: {case['filename']}")
                print(f"      Title: {case['title']}")
                print()
            
            if case_list:
                closest_case = case_list[0]
                case_url = base_url + closest_case['filename']
                
                print(f"✅ Testing closest case: {closest_case['citation']}")
                print(f"🔍 URL: {case_url}")
                
                # Try to access this case
                try:
                    case_response = requests.get(case_url, headers=headers, timeout=10)
                    
                    if case_response.status_code == 200:
                        case_content = case_response.text
                        
                        # Extract title
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', case_content, re.IGNORECASE)
                        if title_match:
                            print(f"📋 HTML Title: {title_match.group(1)}")
                        
                        print(f"✅ SUCCESS: Case accessible at {case_url}")
                        
                        # Check if this could be a reasonable match for "Smith v. Jones"
                        if 'smith' in closest_case['title'].lower() or 'jones' in closest_case['title'].lower():
                            print(f"🎯 GOOD MATCH: Case name contains keywords from extracted name!")
                        
                        return case_url
                        
                    else:
                        print(f"❌ HTTP error: {case_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error accessing case: {e}")
            
            # Also check if there are any cases with page numbers in the 580s
            print(f"\n🔍 Looking for cases with pages 580-590:")
            nearby_cases = [case for case in case_list if 580 <= case['page'] <= 590]
            
            if nearby_cases:
                print(f"✅ Found {len(nearby_cases)} cases in target range:")
                for case in nearby_cases:
                    print(f"   {case['citation']} - {case['title']}")
            else:
                print("❌ No cases found with pages 580-590")
                
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = find_case_by_file_links()
    
    if result:
        print(f"\n✅ Found working case URL: {result}")
    else:
        print("\n❌ No suitable case found")
