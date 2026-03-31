#!/usr/bin/env python3
"""
Check what the frontend actually received for the Foss case
"""

import requests
import json

def check_foss_in_frontend():
    """Check the actual citation data from the frontend"""
    
    # The D2 document was processed, let's check the task status
    task_id = "client-1762217584794-p83vuztsx"
    
    try:
        url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("🔍 CHECKING FOSS CASE IN FRONTEND DATA")
            print("=" * 50)
            
            citations = data.get('citations', [])
            print(f"Total citations: {len(citations)}")
            
            # Find the Foss case
            foss_citation = None
            for c in citations:
                if '161 F.3d 584' in c.get('citation', ''):
                    foss_citation = c
                    break
            
            if foss_citation:
                print(f"\n✅ Found Foss citation:")
                print(f"  Citation: {foss_citation.get('citation', 'N/A')}")
                print(f"  Verified: {foss_citation.get('verified', False)}")
                print(f"  Source: {foss_citation.get('verification_source', 'N/A')}")
                print(f"  Confidence: {foss_citation.get('confidence', 0):.2f}")
                print(f"  Extracted name: {foss_citation.get('extracted_case_name', 'N/A')}")
                print(f"  Canonical name: {foss_citation.get('canonical_name', 'N/A')}")
                print(f"  Error: {foss_citation.get('error', 'None')}")
                
                # Check all verification fields
                print(f"\n🔍 All verification fields:")
                for key, value in foss_citation.items():
                    if 'verif' in key.lower() or 'canonical' in key.lower() or key in ['verified', 'source', 'confidence']:
                        print(f"  {key}: {value}")
                        
                # Determine why it shows as unverified
                is_verified = foss_citation.get('verified', False)
                confidence = foss_citation.get('confidence', 0)
                extracted_name = foss_citation.get('extracted_case_name', 'N/A')
                
                print(f"\n🎯 VERDICT:")
                if not is_verified:
                    print("❌ Citation shows as unverified because:")
                    if extracted_name == 'N/A':
                        print("   - Case name extraction failed (N/A)")
                    if confidence < 0.7:
                        print(f"   - Low confidence score ({confidence:.2f})")
                    print("   - Frontend may have threshold for displaying verification")
                else:
                    print("✅ Citation is properly verified")
                    
            else:
                print("❌ Foss citation not found in results")
                
                # Show first few citations to debug
                print(f"\n📋 First 5 citations:")
                for i, c in enumerate(citations[:5]):
                    print(f"  {i+1}. {c.get('citation', 'N/A')}")
                    
        else:
            print(f"❌ Failed to get task status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_foss_in_frontend()
