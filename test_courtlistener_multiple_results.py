#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to check if CourtListener returns multiple results for 136 S. Ct. 1083
"""

import requests
import json
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_courtlistener_multiple_results():
    """Test if CourtListener returns multiple results for 136 S. Ct. 1083"""
    
    # CourtListener API configuration
    api_key = "***REDACTED_COURTLISTENER_KEY***"  # From previous tests
    base_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test the problematic citation
    citation = "136 S. Ct. 1083"
    
    print(f"Testing CourtListener API for citation: {citation}")
    print(f"API endpoint: {base_url}")
    print()
    
    try:
        # Make the API request
        data = {"text": citation}
        response = requests.post(base_url, headers=headers, json=data, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            
            print(f"Number of results returned: {len(results)}")
            print()
            
            # Show all results
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                
                # Extract cluster information
                clusters = result.get('clusters', [])
                if clusters:
                    cluster = clusters[0]  # First cluster
                    case_name = cluster.get('case_name', 'N/A')
                    date_filed = cluster.get('date_filed', 'N/A')
                    docket_number = cluster.get('docket_number', 'N/A')
                    
                    print(f"  Case name: {case_name}")
                    print(f"  Date filed: {date_filed}")
                    print(f"  Docket number: {docket_number}")
                    print(f"  URL: {cluster.get('absolute_url', 'N/A')}")
                else:
                    print(f"  No clusters found")
                
                print()
            
            # Check if both Luis and Friedrichs cases are returned
            case_names = []
            for result in results:
                clusters = result.get('clusters', [])
                for cluster in clusters:
                    case_name = cluster.get('case_name', '')
                    case_names.append(case_name)
            
            print("="*60)
            print("ANALYSIS:")
            print(f"All case names found: {case_names}")
            
            luis_found = any('Luis' in name for name in case_names)
            friedrichs_found = any('Friedrichs' in name for name in case_names)
            
            print(f"Luis v. United States found: {luis_found}")
            print(f"Friedrichs v. Cal. Teachers Ass'n found: {friedrichs_found}")
            
            if luis_found and friedrichs_found:
                print("✅ CONFIRMED: CourtListener returns BOTH cases for 136 S. Ct. 1083")
                print("   This explains why the system gets the wrong canonical data!")
            elif friedrichs_found and not luis_found:
                print("❌ Only Friedrichs case found - this explains the wrong data")
            elif luis_found and not friedrichs_found:
                print("✅ Only Luis case found - this would be correct")
            else:
                print("❓ Neither case found - unexpected result")
                
        else:
            print(f"API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error making API request: {e}")

if __name__ == '__main__':
    test_courtlistener_multiple_results()
