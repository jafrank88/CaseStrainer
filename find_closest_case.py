#!/usr/bin/env python3
"""
Find the case on Law Resource.org closest to page 584
"""

import requests
import re

def find_closest_case():
    """Find the case closest to page 584 in F.3d volume 161"""
    
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
            
            # Extract the table rows with case information
            # Look for pattern: <tr about="..."><td class="case_cite">161 F.3d 584</td><td class="date">...</td>...
            row_pattern = r'<tr about="[^"]*">\s*<td class="case_cite">([^<]+)</td>\s*<td class="date">([^<]+)</td>'
            matches = re.findall(row_pattern, content)
            
            print(f"📊 Found {len(matches)} cases in volume")
            
            closest_case = None
            closest_diff = float('inf')
            
            for citation, date in matches:
                # Extract page number from citation
                page_match = re.search(r'F\.?3d\s+(\d+)', citation)
                if page_match:
                    page = int(page_match.group(1))
                    diff = abs(page - target_page)
                    
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_case = {
                            'citation': citation,
                            'page': page,
                            'date': date,
                            'diff': diff
                        }
            
            if closest_case:
                print(f"\n✅ Closest case found:")
                print(f"   Citation: {closest_case['citation']}")
                print(f"   Page: {closest_case['page']}")
                print(f"   Date: {closest_case['date']}")
                print(f"   Difference: {closest_case['diff']} pages")
                
                # Try to access this case
                case_url = f"{base_url}{closest_case['page']}"
                print(f"\n🔍 Testing case URL: {case_url}")
                
                try:
                    case_response = requests.get(case_url, headers=headers, timeout=10)
                    
                    if case_response.status_code == 200:
                        case_content = case_response.text
                        
                        # Extract title
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', case_content, re.IGNORECASE)
                        if title_match:
                            print(f"📋 Title: {title_match.group(1)}")
                        
                        # Look for case name in content
                        case_name_patterns = [
                            r'([A-Z][a-zA-Z\s&\-\']+\.?\s+v\.?\s+[A-Z][a-zA-Z\s&\-\']+\.?)',
                            r'<h1[^>]*>([^<]+)</h1>',
                        ]
                        
                        for pattern in case_name_patterns:
                            name_matches = re.findall(pattern, case_content)
                            for match in name_matches:
                                if 'v.' in match.lower() and len(match.strip()) > 10:
                                    print(f"👥 Case name: {match.strip()}")
                        
                        print(f"✅ SUCCESS: Case accessible at {case_url}")
                        return case_url
                        
                    else:
                        print(f"❌ HTTP error: {case_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error accessing case: {e}")
            
            # Show some nearby cases for reference
            print(f"\n📋 Showing cases near page {target_page}:")
            nearby_cases = []
            
            for citation, date in matches[:20]:  # Check first 20 cases
                page_match = re.search(r'F\.?3d\s+(\d+)', citation)
                if page_match:
                    page = int(page_match.group(1))
                    if abs(page - target_page) <= 10:  # Within 10 pages
                        nearby_cases.append((citation, page, date, abs(page - target_page)))
            
            nearby_cases.sort(key=lambda x: x[3])  # Sort by distance
            
            for citation, page, date, diff in nearby_cases[:5]:
                print(f"   {citation} (page {page}, {date}) - {diff} pages away")
                
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = find_closest_case()
    
    if result:
        print(f"\n✅ Found working case URL: {result}")
    else:
        print("\n❌ No suitable case found")
