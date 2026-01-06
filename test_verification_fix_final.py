"""
Test if verification works after fixing models.py
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("TESTING VERIFICATION FIX - AFTER FIXING MODELS.PY")
print("=" * 80)
print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# First check if the service needs restart
print("Checking if service picked up the change...")
try:
    # Test with a simple citation that should verify
    test_text = "See 578 U.S. 5 (2016) for details."
    
    response = requests.post(
        'http://localhost:5000/casestrainer/api/analyze',
        json={'text': test_text}
    )
    
    if response.status_code == 200:
        data = response.json()
        citations = data.get('citations', [])
        
        if citations:
            citation = citations[0]
            print(f"Test citation: {citation.get('citation')}")
            print(f"Verified: {citation.get('verified')}")
            print(f"Has canonical data: {bool(citation.get('canonical_name'))}")
            
            if citation.get('verified'):
                print("\n✅ SUCCESS: Verification is working!")
            else:
                print("\n⚠️  Verification still not working - may need service restart")
        else:
            print("No citations found in test")
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Error testing: {e}")

print("\n" + "=" * 80)
print("If verification is still not working, the service needs to be restarted.")
print("The changes have been applied to both:")
print("1. unified_processing_pipeline.py - enable_verification=True")
print("2. models.py - ProcessingConfig.enable_verification=True")
print("=" * 80)
