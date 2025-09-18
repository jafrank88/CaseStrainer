#!/usr/bin/env python3
"""
Debug script to see what Bing is extracting and why it's contaminated
"""

import requests
import re
from urllib.parse import quote

def debug_bing_extraction():
    """Debug what Bing is extracting"""
    citation_text = "183 Wn.2d 649"
    extracted_case_name = "that and by the . Lopez Demetrio v. Sakuma Bros. Farms"
    
    search_query = f"{citation_text} {extracted_case_name}"
    search_url = f"https://www.bing.com/search?q={quote(search_query)}"
    
    print(f"Search URL: {search_url}")
    print(f"Citation: {citation_text}")
    print(f"Extracted: {extracted_case_name}")
    print()
    
    try:
        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            print("=== BING SEARCH RESULTS ===")
            
            # Extract search results
            result_pattern = r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>'
            results = re.findall(result_pattern, response.text, re.DOTALL | re.IGNORECASE)
            
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                print(f"\n--- Result {i} ---")
                
                # Extract caption
                caption_match = re.search(r'<div[^>]*class="[^"]*b_caption[^"]*"[^>]*>(.*?)</div>', result, re.DOTALL | re.IGNORECASE)
                if caption_match:
                    caption_text = re.sub(r'<[^>]+>', '', caption_match.group(1)).strip()
                    print(f"Caption: {caption_text[:200]}...")
                    
                    # Check if citation is in this result
                    if citation_text.replace(' ', '').lower() in caption_text.replace(' ', '').lower():
                        print("✅ Citation found in this result")
                        
                        # Try to extract case name using the same patterns as the verifier
                        case_patterns = [
                            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith v. Jones
                            r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # In re Smith
                            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Petition\s+for\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith Petition for Jones
                        ]
                        
                        extracted_case = None
                        for pattern in case_patterns:
                            match = re.search(pattern, caption_text)
                            if match:
                                extracted_case = match.group(1).strip()
                                print(f"Extracted case name: {extracted_case}")
                                break
                        
                        if not extracted_case:
                            print("❌ No case name extracted")
                        elif extracted_case == extracted_case_name:
                            print("⚠️  CONTAMINATION: Extracted case name matches original extracted name")
                        else:
                            print(f"✅ Different case name: {extracted_case}")
                    else:
                        print("❌ Citation not found in this result")
                else:
                    print("❌ No caption found")
        else:
            print(f"Bing search failed: {response.status_code}")
            
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == '__main__':
    debug_bing_extraction()









