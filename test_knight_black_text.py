#!/usr/bin/env python3
"""
Test script to test the case name extraction fix with the problematic text
"""

import requests
import json

def test_knight_black_text():
    """Test the API with the text that has incorrect case name assignment"""
    
    # The problematic text from the user
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
    
    print("🔍 Testing Knight/Black Case Name Extraction Fix")
    print("=" * 60)
    print(f"Test text length: {len(test_text)} characters")
    print(f"Test text preview: {test_text[:100]}...")
    print()
    
    try:
        # Test the API endpoint
        url = "http://localhost:5000/casestrainer/api/analyze"
        payload = {
            "text": test_text,
            "type": "text"
        }
        
        print(f"📡 Sending request to: {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            print(f"📊 Citations found: {len(result.get('result', {}).get('citations', []))}")
            print(f"📊 Clusters found: {len(result.get('result', {}).get('clusters', []))}")
            
            # Show all citations with their case names
            citations = result.get('result', {}).get('citations', [])
            print(f"\n🔍 Citation Analysis:")
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print(f"  Text: {citation.get('citation', 'N/A')}")
                print(f"  Case: {citation.get('case_name', 'N/A')}")
                print(f"  Extracted Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"  Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                
            # Show clusters
            clusters = result.get('result', {}).get('clusters', [])
            print(f"\n🔍 Cluster Analysis:")
            for i, cluster in enumerate(clusters, 1):
                print(f"\nCluster {i}:")
                print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                print(f"  Citations: {cluster.get('citations', [])}")
                print(f"  Size: {cluster.get('size', 'N/A')}")
                print(f"  Year: {cluster.get('year', 'N/A')}")
                
            # Expected case name assignments
            expected_assignments = {
                "178 Wn. App. 929": "In re Vulnerable Adult Petition for Knight",
                "317 P.3d 1068": "In re Vulnerable Adult Petition for Knight", 
                "188 Wn.2d 114": "In re Marriage of Black",
                "392 P.3d 1041": "In re Marriage of Black",
                "155 Wn. App. 715": "Blackmon v. Blackmon",
                "230 P.3d 233": "Blackmon v. Blackmon"
            }
            
            print(f"\n📋 Expected Case Name Assignments:")
            for citation, expected_case in expected_assignments.items():
                print(f"  - {citation} → {expected_case}")
                
            # Check if assignments are correct
            print(f"\n🔍 Assignment Accuracy Check:")
            correct_assignments = 0
            total_assignments = len(expected_assignments)
            
            for citation in citations:
                citation_text = citation.get('citation', '')
                actual_case = citation.get('case_name', 'N/A')
                expected_case = expected_assignments.get(citation_text, 'Unknown')
                
                if actual_case == expected_case:
                    print(f"  ✅ {citation_text} → {actual_case}")
                    correct_assignments += 1
                else:
                    print(f"  ❌ {citation_text} → {actual_case} (Expected: {expected_case})")
                    
            accuracy = (correct_assignments / total_assignments) * 100
            print(f"\n📈 Assignment Accuracy: {correct_assignments}/{total_assignments} = {accuracy:.1f}%")
            
            if accuracy == 100:
                print("🎉 All case name assignments are correct!")
            else:
                print("⚠️  Some case name assignments are incorrect - the fix may need more work")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knight_black_text()
