#!/usr/bin/env python3
"""
Test the cross-contamination fix with specific citations
"""
import requests
import json

def test_specific_cross_contamination():
    """Test the specific cross-contamination issue mentioned by user"""
    
    # Test text with the problematic citations
    test_text = """
    A & G Constr. Co. v. Reid Bros. Logging Co., 547 P.2d 1207 (1976).
    State v. Bayer Corp., 32 So. 3d 496 (2010).
    """
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        'type': 'text',
        'text': test_text,
        'client_request_id': 'test-specific-cross-contamination'
    }
    
    print("🔍 Testing specific cross-contamination issue:")
    print("="*60)
    print(f"Test text: {test_text.strip()}")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            clusters = result.get('result', {}).get('clusters', [])
            
            print(f"\n✅ SUCCESS!")
            print(f"📝 Citations found: {len(citations)}")
            print(f"📚 Clusters found: {len(clusters)}")
            
            # Check for the specific cross-contamination issue
            print(f"\n🔍 Checking for specific cross-contamination:")
            
            for i, c in enumerate(citations, 1):
                citation_text = c.get('citation', 'N/A')
                extracted_name = c.get('extracted_case_name', 'N/A')
                extracted_date = c.get('extracted_date', 'N/A')
                canonical_name = c.get('canonical_name', 'N/A')
                canonical_date = c.get('canonical_date', 'N/A')
                verified = c.get('verified', False)
                
                print(f"\n  {i}. Citation: {citation_text}")
                print(f"     Extracted: {extracted_name} ({extracted_date})")
                print(f"     Canonical: {canonical_name} ({canonical_date})")
                print(f"     Verified: {verified}")
                
                # Check for the specific issue mentioned by user
                if citation_text == "547 P.2d 1207":
                    if canonical_name and "Bayer" in canonical_name:
                        print(f"     ❌ CROSS-CONTAMINATION: 547 P.2d 1207 has Bayer canonical name!")
                        return False
                    else:
                        print(f"     ✅ CORRECT: 547 P.2d 1207 has appropriate canonical name")
                
                if citation_text == "32 So. 3d 496":
                    if canonical_name and "A & G" in canonical_name or "Reid Bros" in canonical_name:
                        print(f"     ❌ CROSS-CONTAMINATION: 32 So. 3d 496 has A & G canonical name!")
                        return False
                    else:
                        print(f"     ✅ CORRECT: 32 So. 3d 496 has appropriate canonical name")
            
            print(f"\n✅ NO CROSS-CONTAMINATION ISSUES DETECTED!")
            return True
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_specific_cross_contamination()
    if success:
        print("\n🎉 Specific cross-contamination fix test PASSED!")
    else:
        print("\n💥 Specific cross-contamination fix test FAILED!")

