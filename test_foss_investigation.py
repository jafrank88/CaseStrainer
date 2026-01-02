#!/usr/bin/env python3
"""
Investigate why FOSS v. NATIONAL MARINE FISHERIES SERVICE citation failed
"""

import requests
import json

def test_foss_citation():
    """Test the specific FOSS citation that failed"""
    
    print("🔍 INVESTIGATING FOSS CITATION FAILURE")
    print("=" * 50)
    
    # Test the exact citation text
    foss_text = "FOSS v. NATIONAL MARINE FISHERIES SERVICE, 161 F.3d 584 (9th Cir. 1998)"
    
    print(f"📋 Testing citation: {foss_text}")
    
    # Test with minimal text to isolate the issue
    test_text = f"This case involves {foss_text}."
    
    try:
        response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
            json={
                'type': 'text', 
                'text': test_text, 
                'enable_verification': True
            }, 
            timeout=30)

        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Citations found: {len(citations)}")
            
            for i, cit in enumerate(citations):
                print(f"\n🔎 Citation {i+1}:")
                print(f"   Citation text: {cit.get('citation')}")
                print(f"   Extracted case name: {cit.get('extracted_case_name')}")
                print(f"   Verified: {cit.get('verified')}")
                print(f"   Canonical name: {cit.get('canonical_name')}")
                print(f"   Verification status: {cit.get('metadata', {}).get('verification_status')}")
                print(f"   Error: {cit.get('error')}")
                print(f"   Method: {cit.get('method')}")
                print(f"   Context: {cit.get('context')}")
                
                # Check if it's the FOSS citation
                if '161 F.3d 584' in cit.get('citation', ''):
                    print(f"\n🎯 FOUND FOSS CITATION:")
                    print(f"   ❌ Issue: Extracted as '{cit.get('extracted_case_name')}' instead of proper case name")
                    print(f"   ❌ Issue: Verification failed")
                    
        else:
            print(f"API Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Also test the citation directly with verification master
    print(f"\n🧪 TESTING DIRECT VERIFICATION:")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.unified_verification_master import get_master_verifier
        import asyncio
        
        async def test_direct():
            verifier = get_master_verifier()
            result = await verifier.verify_citations_batch(
                ["161 F.3d 584"], 
                ["FOSS v. NATIONAL MARINE FISHERIES SERVICE"], 
                ["1998"]
            )
            
            if result and len(result) > 0:
                citation = result[0]
                print(f"   Direct verification result:")
                print(f"   Verified: {getattr(citation, 'verified', 'N/A')}")
                print(f"   Canonical name: {getattr(citation, 'canonical_name', 'N/A')}")
                print(f"   Error: {getattr(citation, 'error', 'N/A')}")
            else:
                print("   No direct verification result")
        
        asyncio.run(test_direct())
        
    except Exception as e:
        print(f"Direct verification error: {e}")

if __name__ == "__main__":
    test_foss_citation()
