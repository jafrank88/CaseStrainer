#!/usr/bin/env python3
"""
Test case name extraction for Spokeo citations to debug truncation issue.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_spokeo_citations():
    """Test case name extraction for Spokeo citations."""
    
    # Test with the specific citations from the user
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016) that standing requirements cannot be erased.'
    
    test_cases = [
        {"citation": "136 S. Ct. 1540", "expected": "Spokeo, Inc. v. Robins"},
        {"citation": "194 L. Ed. 2d 635", "expected": "Spokeo, Inc. v. Robins"}
    ]
    
    print("🔍 TESTING SPOKEO CASE NAME EXTRACTION")
    print("=" * 70)
    print(f"📝 Text: {text}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        print(f"{i}. Testing citation: '{citation}'")
        print(f"   Expected: '{expected}'")
        
        # Find citation position in text
        start_index = text.find(citation)
        end_index = start_index + len(citation)
        
        if start_index == -1:
            print(f"   ❌ Citation not found in text")
            continue
            
        print(f"   Position: {start_index}-{end_index}")
        
        # Test the master extraction function
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            result = extract_case_name_and_date_master(
                text=text,
                citation=citation,
                citation_start=start_index,
                citation_end=end_index,
                debug=False
            )
            
            extracted_name = result.get('case_name', 'None')
            print(f"   Master extraction: '{extracted_name}'")
            
            # Test the cleaning function
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            
            cleaned_name = processor._clean_extracted_case_name(extracted_name)
            print(f"   After cleaning: '{cleaned_name}'")
            
            # Check if it matches expected
            if cleaned_name == expected:
                print(f"   ✅ CORRECT")
            else:
                print(f"   ❌ INCORRECT - Expected '{expected}', got '{cleaned_name}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()

    # Test the full API pipeline
    print("🧪 TESTING FULL API PIPELINE")
    print("=" * 70)
    
    try:
        import requests
        
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "text", "text": text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"📊 API returned {len(citations)} citations:")
            for citation in citations:
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                verified = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                
                print(f"   {citation_text}: '{case_name}' (verified={verified}, parallel={true_by_parallel})")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API Test Error: {e}")

if __name__ == "__main__":
    test_spokeo_citations()
