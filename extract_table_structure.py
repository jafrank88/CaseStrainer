#!/usr/bin/env python3
"""
Extract the actual table structure from Law Resource.org
"""

import requests
import re

def extract_table_structure():
    """Extract and analyze the table structure"""
    
    base_url = "https://law.resource.org/pub/us/case/reporter/F3/161/"
    
    print(f"🔍 Analyzing table structure at: {base_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Find the table section
            table_start = content.find('<table class="filelist index">')
            if table_start != -1:
                table_section = content[table_start:table_start + 5000]  # Get first 5000 chars of table
                print("📊 Found table structure:")
                print("=" * 50)
                print(table_section[:2000])
                print("=" * 50)
                
                # Look for all <tr> tags in the table
                tr_pattern = r'<tr[^>]*>(.*?)</tr>'
                tr_matches = re.findall(tr_pattern, table_section, re.DOTALL)
                
                print(f"\n📊 Found {len(tr_matches)} table rows")
                
                # Extract first few rows to understand structure
                for i, row in enumerate(tr_matches[:5]):
                    print(f"\n--- Row {i+1} ---")
                    # Extract all <td> content from this row
                    td_pattern = r'<td[^>]*class="([^"]*)"[^>]*>([^<]*)</td>'
                    td_matches = re.findall(td_pattern, row)
                    for td_class, td_content in td_matches:
                        print(f"   {td_class}: {td_content}")
                
                # Look specifically for page numbers around 584
                print(f"\n🔍 Looking for pages around 584...")
                
                # Extract all page numbers from the table
                page_pattern = r'<td[^>]*class="case_cite"[^>]*>([^<]*)</td>'
                page_matches = re.findall(page_pattern, table_section)
                
                pages_found = []
                for page_text in page_matches:
                    page_match = re.search(r'(\d+)', page_text)
                    if page_match:
                        page_num = int(page_match.group(1))
                        if 570 <= page_num <= 600:  # Around page 584
                            pages_found.append((page_text, page_num))
                
                if pages_found:
                    print(f"✅ Found pages near 584:")
                    for page_text, page_num in pages_found:
                        print(f"   {page_text}")
                else:
                    print("❌ No pages found near 584")
                    
                    # Show some example pages
                    print(f"\n📋 First 10 pages found:")
                    for i, page_text in enumerate(page_matches[:10]):
                        page_match = re.search(r'(\d+)', page_text)
                        if page_match:
                            print(f"   {page_text} -> page {page_match.group(1)}")
                
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    extract_table_structure()
