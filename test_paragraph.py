#!/usr/bin/env python3
"""
Test script to test the specific paragraph provided by the user.
"""

import requests
import json

def test_paragraph():
    """Test the paragraph with Black and Knight citations."""
    
    paragraph = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("Testing paragraph with Black and Knight citations...")
    print(f"Paragraph length: {len(paragraph)} characters")
    print("-" * 80)
    
    # Test the API endpoint
    url = "http://localhost:8080/casestrainer/api/analyze"
    
    data = {
        "text": paragraph,
        "options": {
            "extract_citations": True,
            "verify_citations": True,
            "cluster_citations": True
        }
    }
    
    try:
        print("Making request to backend API...")
        response = requests.post(url, json=data, timeout=60)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            
            # Print summary
            print(f"\nSummary:")
            print(f"- Citations found: {len(result.get('result', {}).get('citations', []))}")
            print(f"- Clusters found: {len(result.get('result', {}).get('clusters', []))}")
            
            # Print citation details for Black and Knight
            citations = result.get('result', {}).get('citations', [])
            
            print(f"\n🔍 Citation Analysis:")
            for citation in citations:
                citation_text = citation.get('citation', '')
                case_name = citation.get('extracted_case_name', citation.get('case_name', ''))
                canonical_name = citation.get('canonical_name', 'None')
                canonical_date = citation.get('canonical_date', 'None')
                source = citation.get('source', 'None')
                verified = citation.get('verified', False)
                
                # Check if this is a Black or Knight citation
                is_black = 'black' in case_name.lower() if case_name else False
                is_knight = 'knight' in case_name.lower() if case_name else False
                
                if is_black or is_knight:
                    status = "✅ VERIFIED" if verified else "❌ NOT VERIFIED"
                    case_type = "🏴 BLACK" if is_black else "⚔️ KNIGHT"
                    print(f"\n{case_type} {status}")
                    print(f"  Citation: {citation_text}")
                    print(f"  Extracted: {case_name}")
                    print(f"  Canonical: {canonical_name}")
                    print(f"  Date: {canonical_date}")
                    print(f"  Source: {source}")
                
            # Print cluster details
            clusters = result.get('result', {}).get('clusters', [])
            print(f"\n📁 Cluster Analysis:")
            for cluster in clusters:
                cluster_id = cluster.get('cluster_id', '')
                extracted_name = cluster.get('extracted_case_name', '')
                canonical_name = cluster.get('canonical_name', 'None')
                verification_status = cluster.get('verification_status', 'unknown')
                size = cluster.get('size', 0)
                
                # Check if this is a Black or Knight cluster
                is_black = 'black' in extracted_name.lower() if extracted_name else False
                is_knight = 'knight' in extracted_name.lower() if extracted_name else False
                
                if is_black or is_knight:
                    case_type = "🏴 BLACK" if is_black else "⚔️ KNIGHT"
                    print(f"\n{case_type} Cluster:")
                    print(f"  ID: {cluster_id}")
                    print(f"  Extracted: {extracted_name}")
                    print(f"  Canonical: {canonical_name}")
                    print(f"  Status: {verification_status}")
                    print(f"  Size: {size} citations")
            
            # Save full response for detailed analysis
            with open('test_paragraph_response.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full response saved to test_paragraph_response.json")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_paragraph()

