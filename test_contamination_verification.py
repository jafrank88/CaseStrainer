#!/usr/bin/env python3

import requests
import json

def test_contamination_verification():
    """Test that extracted and canonical names remain separate."""
    
    # Test with a known case that should extract properly
    test_text = '''State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022).'''
    
    print("CONTAMINATION VERIFICATION TEST")
    print("=" * 60)
    print(f"Text: {test_text}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            # Debug: Print raw response to see where case_name is coming from
            print("DEBUG: Raw first citation:")
            if citations:
                import json
                print(json.dumps(citations[0], indent=2))
            print()
            
            print(f"Found {len(citations)} citations")
            print()
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                
                print(f"Citation {i}: {citation_text}")
                print(f"  case_name: '{case_name}'")
                print(f"  extracted_case_name: '{extracted_case_name}'")
                print(f"  canonical_name: '{canonical_name}'")
                print(f"  cluster_case_name: '{cluster_case_name}'")
                
                # Check for contamination
                contamination_detected = False
                
                if case_name != 'N/A' and canonical_name != 'N/A' and case_name == canonical_name:
                    if extracted_case_name == 'N/A' or extracted_case_name != canonical_name:
                        print("  🚨 CONTAMINATION DETECTED: case_name matches canonical_name but not extracted_case_name")
                        contamination_detected = True
                
                if extracted_case_name == 'Unknown Case':
                    print("  ❌ EXTRACTION FAILURE: extracted_case_name is 'Unknown Case'")
                
                if not contamination_detected:
                    if case_name == extracted_case_name or case_name == cluster_case_name:
                        print("  ✅ NO CONTAMINATION: case_name properly derived from extracted/cluster data")
                    elif case_name == 'N/A':
                        print("  ✅ NO CONTAMINATION: case_name is N/A (no fallback to canonical)")
                
                print()
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_contamination_verification()
