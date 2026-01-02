#!/usr/bin/env python3
"""
Test verification with a simple known citation in sync mode
"""

import requests
import json

def test_sync_verification():
    """Test verification with a simple known citation"""
    
    print("🔧 TESTING SYNC VERIFICATION")
    print("=" * 40)
    
    # Test with a known verifiable citation
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent."
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"📋 Found {len(citations)} citations:")
            
            for i, citation in enumerate(citations):
                print(f"\n  Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"    Verified: {citation.get('verified', 'N/A')}")
                print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"    Canonical URL: {citation.get('canonical_url', 'N/A')}")
                
                # Check verification paradox
                has_canonical = bool(
                    citation.get('canonical_name') and 
                    citation.get('canonical_date') and 
                    citation.get('canonical_url')
                )
                verified = citation.get('verified', False)
                
                if has_canonical and not verified:
                    print(f"    ⚠️  VERIFICATION PARADOX!")
                elif verified and has_canonical:
                    print(f"    ✅ VERIFICATION WORKING!")
                elif has_canonical:
                    print(f"    ℹ️  Has canonical data but not verified")
                else:
                    print(f"    ℹ️  No canonical data found")
            
            # Show metadata
            metadata = result.get('result', {}).get('metadata', {})
            print(f"\n📋 PROCESSING METADATA:")
            print(f"   Processing mode: {metadata.get('processing_mode', 'N/A')}")
            print(f"   Verification count: {metadata.get('verification_count', 'N/A')}")
            print(f"   Stages completed: {metadata.get('stages_completed', 'N/A')}")
            print(f"   Status: {metadata.get('status', 'N/A')}")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_verification()
