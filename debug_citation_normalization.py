#!/usr/bin/env python3
"""
Debug script to test citation normalization for 146 Wn.2d 1, 9, 43 P.3d 4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_citation_normalization():
    """Test how the citation gets normalized in the backend."""
    
    citation = "146 Wn.2d 1, 9, 43 P.3d 4"
    print(f"Original citation: '{citation}'")
    print("=" * 60)
    
    # Test different normalization functions
    try:
        # Test 1: citation_normalizer.py
        from src.citation_normalizer import normalize_citation
        normalized1 = normalize_citation(citation)
        print(f"1. citation_normalizer.normalize_citation: '{normalized1}'")
        
        # Test 2: citation_format_utils.py
        from src.citation_format_utils import normalize_washington_synonyms
        normalized2 = normalize_washington_synonyms(citation)
        print(f"2. citation_format_utils.normalize_washington_synonyms: '{normalized2}'")
        
        # Test 3: citation_utils.py
        from src.citation_utils import normalize_citation_text
        normalized3 = normalize_citation_text(citation)
        print(f"3. citation_utils.normalize_citation_text: '{normalized3}'")
        
        # Test 4: unified_citation_processor_v2.py
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        normalized4 = processor._normalize_citation(citation)
        print(f"4. unified_citation_processor_v2._normalize_citation: '{normalized4}'")
        
        # Test 5: Check if there's a _clean_citation_for_lookup method
        if hasattr(processor, '_clean_citation_for_lookup'):
            try:
                normalized5 = processor._clean_citation_for_lookup(citation)
                print(f"5. _clean_citation_for_lookup: '{normalized5}'")
            except Exception as e:
                print(f"5. _clean_citation_for_lookup: Error - {e}")
        
        # Test 6: Check citation components extraction
        if hasattr(processor, '_extract_citation_components'):
            try:
                components = processor._extract_citation_components(citation)
                print(f"6. _extract_citation_components: {components}")
            except Exception as e:
                print(f"6. _extract_citation_components: Error - {e}")
        
        print("\n" + "=" * 60)
        print("ANALYSIS:")
        print("The citation normalization process transforms the citation before sending to CourtListener.")
        print("This could explain why the wrong case is being returned - the normalized citation")
        print("might match a different case in CourtListener's database.")
        
    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_courtlistener_with_normalized():
    """Test CourtListener API with the normalized citation."""
    
    import requests
    import os
    
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("No CourtListener API key found")
        return
    
    # Test different normalized versions
    test_citations = [
        "146 Wn.2d 1, 9, 43 P.3d 4",  # Original
        "146 Wash. 2d 1, 9, 43 P.3d 4",  # Normalized Wn. -> Wash.
        "146 Wn.2d 1",  # Just the base citation
        "146 Wash. 2d 1",  # Normalized base citation
    ]
    
    headers = {"Authorization": f"Token {api_key}"}
    
    for citation in test_citations:
        print(f"\nTesting normalized citation: '{citation}'")
        print("-" * 40)
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            response = requests.post(url, headers=headers, data={"text": citation}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    citation_data = data[0]
                    if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                        cluster = citation_data['clusters'][0]
                        case_name = cluster.get('case_name', 'N/A')
                        print(f"  Found: {case_name}")
                        
                        # Check if this matches expected case
                        expected = "Dep't of Ecology v. Campbell & Gwinn, LLC"
                        if expected.lower() in case_name.lower():
                            print(f"  ✅ MATCHES EXPECTED CASE!")
                        else:
                            print(f"  ❌ DOES NOT MATCH EXPECTED CASE")
                    else:
                        print(f"  No clusters found")
                else:
                    print(f"  No results")
            else:
                print(f"  API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    print("DEBUGGING CITATION NORMALIZATION")
    print("=" * 60)
    
    test_citation_normalization()
    test_courtlistener_with_normalized() 