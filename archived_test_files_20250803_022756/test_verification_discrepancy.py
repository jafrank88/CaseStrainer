#!/usr/bin/env python3
"""
Test to investigate why citations that verify with CourtListener now 
were previously marked as "not found in CourtListener"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.courtlistener_verification import verify_with_courtlistener
from src.config import get_config_value
import csv
import json

def test_sample_citations():
    """Test a sample of citations that should be in CourtListener"""
    
    # Sample citations from your JSON that were verified by CourtListener
    test_citations = [
        "94 S. Ct. 1105",    # Davis v. Alaska
        "39 L. Ed. 2d 347",  # Davis v. Alaska  
        "385 U.S. 493",      # Garrity v. New Jersey
        "87 S. Ct. 616",     # Garrity v. New Jersey
        "17 L. Ed. 2d 562",  # Garrity v. New Jersey
        "466 U.S. 668",      # Strickland v. Washington
        "80 L. Ed. 2d 674",  # Strickland v. Washington
        "104 S. Ct. 2052",   # Strickland v. Washington
        "392 U.S. 1",        # Terry v. Ohio
        "88 S. Ct. 1868",    # Terry v. Ohio
    ]
    
    print("TESTING COURTLISTENER VERIFICATION DISCREPANCY")
    print("=" * 60)
    print("Testing citations that should be in CourtListener...")
    print()
    
    api_key = get_config_value("COURTLISTENER_API_KEY", "")
    if not api_key:
        print("ERROR: No CourtListener API key found!")
        return
    
    print(f"Using API key: {api_key[:10]}...")
    print()
    
    results = []
    
    for citation in test_citations:
        print(f"Testing: {citation}")
        try:
            result = verify_with_courtlistener(citation, api_key)
            
            if result and result.get('verified', False):
                print(f"  [VERIFIED]: {result.get('canonical_name', 'Unknown')}")
                print(f"     Date: {result.get('canonical_date', 'Unknown')}")
                print(f"     URL: {result.get('url', 'No URL')}")
                results.append({
                    'citation': citation,
                    'status': 'VERIFIED',
                    'canonical_name': result.get('canonical_name'),
                    'canonical_date': result.get('canonical_date'),
                    'url': result.get('url')
                })
            else:
                print(f"  [NOT FOUND] in CourtListener")
                results.append({
                    'citation': citation,
                    'status': 'NOT_FOUND',
                    'error': result.get('error') if result else 'No result returned'
                })
                
        except Exception as e:
            print(f"  [ERROR]: {str(e)}")
            results.append({
                'citation': citation,
                'status': 'ERROR',
                'error': str(e)
            })
        
        print()
    
    # Summary
    verified_count = sum(1 for r in results if r['status'] == 'VERIFIED')
    not_found_count = sum(1 for r in results if r['status'] == 'NOT_FOUND')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    print("SUMMARY:")
    print("=" * 60)
    print(f"Total citations tested: {len(test_citations)}")
    print(f"Verified by CourtListener: {verified_count}")
    print(f"Not found in CourtListener: {not_found_count}")
    print(f"Errors: {error_count}")
    print()
    
    if verified_count > 0:
        print("[SUCCESS] These citations ARE in CourtListener now!")
        print("   This suggests the original CSV data may be outdated")
        print("   or there was an issue with the original verification run.")
    else:
        print("[FAILURE] None of these citations found in CourtListener")
        print("   This would match the CSV data but contradicts your current results.")
    
    print()
    print("POSSIBLE EXPLANATIONS FOR DISCREPANCY:")
    print("-" * 60)
    print("1. CSV files are from an older run before pipeline improvements")
    print("2. CourtListener API has been updated with more data")
    print("3. Different verification logic was used in the CSV generation")
    print("4. API key or authentication issues in the original run")
    print("5. The original run used a different verification method")
    
    # Save detailed results
    with open('verification_discrepancy_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("Detailed results saved to: verification_discrepancy_results.json")

if __name__ == "__main__":
    test_sample_citations()
