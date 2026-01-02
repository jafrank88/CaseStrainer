#!/usr/bin/env python3
"""
Test specific citation verification issues
"""

import requests
import json

def test_specific_citations():
    """Test the specific citations that should match different cases"""
    
    test_cases = [
        {
            "text": "In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.",
            "expected_case": "Berst v. Snohomish County",
            "citation": "114 Wn. App. 245"
        },
        {
            "text": "In Holland v. City of Tacoma, 90 Wn. App. 533 (1998), the court considered city matters.",
            "expected_case": "Holland v. City of Tacoma", 
            "citation": "90 Wn. App. 533"
        },
        {
            "text": "In Foss v. Nat'l Marine Fisheries Serv., 161 F.3d 584 (9th Cir. 1998), the court ruled on fisheries.",
            "expected_case": "Foss v. Nat'l Marine Fisheries Serv",
            "citation": "161 F.3d 584"
        }
    ]
    
    print("🧪 Testing specific citation verification...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Text: {test_case['text']}")
        print(f"Expected: {test_case['expected_case']}")
        print(f"Citation: {test_case['citation']}")
        
        data = {"text": test_case['text'], "extract_case_names": True}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                
                for citation in citations:
                    if citation.get('citation') == test_case['citation']:
                        print(f"✅ Found citation:")
                        print(f"   Verified: {citation.get('verified', 'N/A')}")
                        print(f"   Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
                        print(f"   Canonical Name: {citation.get('canonical_name', 'N/A')}")
                        print(f"   Canonical Date: {citation.get('canonical_date', 'N/A')}")
                        print(f"   Source: {citation.get('source', 'N/A')}")
                        
                        # Check if it matches expected (more lenient comparison)
                        canonical_name = citation.get('canonical_name', '')
                        if canonical_name:
                            # Normalize both names for comparison
                            expected_normalized = test_case['expected_case'].lower().replace('.', '').replace("'", '')
                            canonical_normalized = canonical_name.lower().replace('.', '').replace("'", '')
                            
                            # Check if key words match
                            expected_words = set(expected_normalized.split())
                            canonical_words = set(canonical_normalized.split())
                            
                            # Remove common words
                            common_words = {'v', 'vs', 'the', 'of', 'in', 'a', 'an'}
                            expected_words -= common_words
                            canonical_words -= common_words
                            
                            # If at least 60% of words match, consider it correct
                            if expected_words and canonical_words:
                                overlap = len(expected_words & canonical_words) / len(expected_words)
                                if overlap >= 0.6:
                                    print(f"   ✅ CORRECT: Matches expected case ({overlap:.0%} word overlap)")
                                else:
                                    print(f"   ❌ WRONG: Low word overlap ({overlap:.0%}): '{canonical_name}' vs '{test_case['expected_case']}'")
                            else:
                                print(f"   ⚠️  UNCLEAR: Cannot compare '{canonical_name}' vs '{test_case['expected_case']}'")
                        else:
                            print(f"   ❌ WRONG: No canonical name found")
                        break
                else:
                    print(f"❌ Citation not found in results")
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_specific_citations()
