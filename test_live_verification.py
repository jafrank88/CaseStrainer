#!/usr/bin/env python3
"""
Test script to verify the live application is using the updated citation verification
"""

import requests
import json

def test_live_verification():
    """Test the live application's citation verification"""
    
    print("=== Testing Live Application Citation Verification ===")
    
    # Test text with citations that should be verified
    test_text = """We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"""
    
    # API endpoint
    url = "http://localhost:5001/casestrainer/api/citations/analyze"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "text": test_text,
        "document_type": "legal_brief"
    }
    
    print(f"Testing URL: {url}")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        print("\nSending request...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\nSuccess! Processing completed")
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
            
            # Check verification status
            verified_count = 0
            total_count = len(result.get('citations', []))
            
            print(f"\n=== CITATION VERIFICATION STATUS ===")
            for i, citation in enumerate(result.get('citations', []), 1):
                verified = citation.get('verified', False)
                source = citation.get('source', 'Unknown')
                canonical_name = citation.get('canonical_name')
                canonical_date = citation.get('canonical_date')
                
                if verified:
                    verified_count += 1
                    status = "✅ VERIFIED"
                else:
                    status = "❌ NOT VERIFIED"
                
                print(f"{i}. {citation.get('citation')} - {status}")
                print(f"   Source: {source}")
                print(f"   Canonical name: {canonical_name}")
                print(f"   Canonical date: {canonical_date}")
                print()
            
            print(f"=== SUMMARY ===")
            print(f"Total citations: {total_count}")
            print(f"Verified citations: {verified_count}")
            print(f"Verification rate: {verified_count/total_count*100:.1f}%" if total_count > 0 else "N/A")
            
            if verified_count > 0:
                print("\n🎉 SUCCESS: Citation verification is working!")
            else:
                print("\n⚠️  WARNING: No citations were verified")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the application")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_live_verification() 