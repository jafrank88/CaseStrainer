#!/usr/bin/env python3
"""
Direct backend test to identify false positive citation extraction.
"""

import requests
import json

def test_backend_direct():
    """Test the backend directly to identify false positives."""
    
    # Test with the exact paragraph that's causing issues
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("🔍 Testing Backend Directly")
    print("=" * 60)
    print(f"Test text length: {len(test_text)} characters")
    print("-" * 60)
    
    # Make request to backend
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    data = {
        "text": test_text,
        "options": {
            "extract_citations": True,
            "verify_citations": True,
            "cluster_citations": True
        }
    }
    
    try:
        print("📡 Making request to backend...")
        response = requests.post(url, json=data, timeout=60)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Request successful!")
                
                # Analyze the results
                citations = result.get('result', {}).get('citations', [])
                clusters = result.get('result', {}).get('clusters', [])
                
                print(f"\n📋 Summary:")
                print(f"- Citations found: {len(citations)}")
                print(f"- Clusters found: {len(clusters)}")
                
                # Check for the problematic citation
                print(f"\n🚨 Checking for False Positives:")
                problematic_citations = []
                
                for citation in citations:
                    citation_text = citation.get('citation', '')
                    extracted_name = citation.get('extracted_case_name', '')
                    canonical_name = citation.get('canonical_name', '')
                    
                    # Check if this citation text exists in the original text
                    if citation_text in test_text:
                        print(f"✅ {citation_text} - FOUND in text")
                        print(f"   Extracted: {extracted_name}")
                        print(f"   Canonical: {canonical_name}")
                    else:
                        print(f"❌ {citation_text} - NOT FOUND in text!")
                        print(f"   Extracted: {extracted_name}")
                        print(f"   Canonical: {canonical_name}")
                        problematic_citations.append(citation)
                
                # Check for the specific problematic case
                print(f"\n🔍 Checking for 'Gillian Timaeus' case:")
                for citation in citations:
                    if 'Gillian Timaeus' in str(citation.get('canonical_name', '')):
                        print(f"🚨 FALSE POSITIVE DETECTED!")
                        print(f"   Citation: {citation.get('citation')}")
                        print(f"   Canonical: {citation.get('canonical_name')}")
                        print(f"   Extracted: {citation.get('extracted_case_name')}")
                        print(f"   Source: {citation.get('source')}")
                        print(f"   This case is NOT in the original text!")
                
                # Save full response for analysis
                with open('backend_test_response.json', 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n💾 Full response saved to backend_test_response.json")
                
                if problematic_citations:
                    print(f"\n⚠️  Found {len(problematic_citations)} problematic citations!")
                    return problematic_citations
                else:
                    print(f"\n✅ All citations appear to be valid!")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Response text: {response.text[:500]}")
                return None
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    problematic = test_backend_direct()
    
    if problematic:
        print(f"\n🚨 SUMMARY: Found {len(problematic)} problematic citations!")
        print("These need to be investigated and fixed in the backend.")
    elif problematic is None:
        print("\n❌ Test failed - could not complete analysis.")
    else:
        print("\n✅ Test completed - no issues found.")
