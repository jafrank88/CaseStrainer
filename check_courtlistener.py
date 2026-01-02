#!/usr/bin/env python3
"""
Check what case CourtListener finds for 57 P.3d 273
"""

import requests
import json

def check_courtlistener():
    """Check CourtListener API for specific citation"""
    
    citation = "57 P.3d 273"
    url = f"https://www.courtlistener.com/api/rest/v4/search/?citation={citation.replace(' ', '%20')}"
    
    print(f"🔍 Checking CourtListener for: {citation}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"\n📊 Found {len(results)} results:")
            
            for i, result in enumerate(results):
                case_name = result.get('caseName', 'N/A')
                citation_found = result.get('citation', 'N/A')
                court = result.get('court', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                url = result.get('absolute_url', 'N/A')
                
                print(f"\n--- Result {i+1} ---")
                print(f"Case Name: {case_name}")
                print(f"Citation: {citation_found}")
                print(f"Court: {court}")
                print(f"Date Filed: {date_filed}")
                print(f"URL: {url}")
                
                # Check if this matches our expected case
                if "Bellevue" in case_name:
                    print(f"✅ MATCH: Found 'Bellevue' case")
                elif "Berst" in case_name:
                    print(f"❌ WRONG: Found 'Berst' case instead of 'Bellevue'")
                else:
                    print(f"⚠️  UNKNOWN: Neither Bellevue nor Berst case")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_courtlistener()
