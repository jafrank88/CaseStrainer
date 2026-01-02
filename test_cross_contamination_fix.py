#!/usr/bin/env python3
"""
Test the cross-contamination fix for Mississippi court PDF
"""
import requests
import json

def test_cross_contamination_fix():
    """Test if the cross-contamination issue is fixed"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        'type': 'url',
        'url': 'https://courts.ms.gov/images/Opinions/CO186333.pdf',
        'client_request_id': 'test-cross-contamination-fix'
    }
    
    print("🔍 Testing cross-contamination fix:")
    print("="*60)
    
    try:
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            clusters = result.get('result', {}).get('clusters', [])
            
            print(f"✅ SUCCESS!")
            print(f"📝 Citations found: {len(citations)}")
            print(f"📚 Clusters found: {len(clusters)}")
            
            # Check for cross-contamination issues
            cross_contamination_found = False
            
            print(f"\n🔍 Checking for cross-contamination issues:")
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
                
                # Check for cross-contamination
                if verified and canonical_name and canonical_name != 'N/A':
                    # Check if canonical name matches extracted name
                    if extracted_name and extracted_name != 'N/A':
                        # Simple similarity check
                        extracted_words = set(extracted_name.lower().split())
                        canonical_words = set(canonical_name.lower().split())
                        
                        # Check for major mismatches
                        if len(extracted_words.intersection(canonical_words)) < 2:
                            print(f"     ⚠️  POTENTIAL CROSS-CONTAMINATION: Names don't match!")
                            cross_contamination_found = True
            
            if cross_contamination_found:
                print(f"\n❌ CROSS-CONTAMINATION ISSUES FOUND!")
            else:
                print(f"\n✅ NO CROSS-CONTAMINATION ISSUES DETECTED!")
            
            return not cross_contamination_found
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_cross_contamination_fix()
    if success:
        print("\n🎉 Cross-contamination fix test PASSED!")
    else:
        print("\n💥 Cross-contamination fix test FAILED!")









