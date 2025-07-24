#!/usr/bin/env python3
"""
Test citation processing directly without the API to isolate the issue.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Prevent use of v3 CourtListener API endpoints
if 'v3' in url:
    print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
    sys.exit(1)

def test_direct_processing():
    """Test citation processing directly using the processor."""
    print("TESTING DIRECT CITATION PROCESSING")
    print("=" * 60)
    
    # Test text with the problematic citation
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    print(f"Test text: {test_text.strip()}")
    print()
    
    try:
        # Try to import and use the processor directly
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        print("✅ Successfully imported UnifiedCitationProcessorV2")
        
        # Create processor with minimal config
        processor = UnifiedCitationProcessorV2()
        print("✅ Successfully created processor")
        
        # Process the text
        print("Processing text...")
        result = processor.process_text(test_text)
        
        print(f"Processing completed")
        
        # Extract citations from result
        citations = []
        if isinstance(result, list):
            # UnifiedCitationProcessorV2 returns List[CitationResult]
            citations = result
        else:
            # Legacy format
            citations = result.get('results', [])
        
        print(f"Found {len(citations)} citations")
        print()
        
        # Display results
        for i, citation in enumerate(citations):
            print(f"Citation {i+1}:")
            
            # Handle both CitationResult objects and dicts
            if hasattr(citation, 'citation'):
                # CitationResult object
                print(f"  Citation: {citation.citation}")
                print(f"  Canonical Name: {citation.canonical_name}")
                print(f"  Canonical Date: {citation.canonical_date}")
                print(f"  URL: {citation.url}")
                print(f"  Verified: {citation.verified}")
                print(f"  Source: {citation.source}")
            else:
                # Dict format
                print(f"  Citation: {citation.get('citation', 'N/A')}")
                print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"  URL: {citation.get('url', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                print(f"  Source: {citation.get('source', 'N/A')}")
            
            # Check for the problematic citation
            citation_text = citation.citation if hasattr(citation, 'citation') else citation.get('citation', '')
            if "146 Wn.2d 1" in citation_text:
                print(f"  *** THIS IS THE PROBLEMATIC CITATION ***")
                canonical_name = citation.canonical_name if hasattr(citation, 'canonical_name') else citation.get('canonical_name', '')
                if canonical_name == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                    print(f"  ✅ CORRECT CASE NAME FOUND!")
                    return True
                else:
                    print(f"  ❌ WRONG CASE NAME: {canonical_name}")
                    return False
            
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_courtlistener_direct():
    """Test CourtListener API directly."""
    print("\nTESTING COURTLISTENER API DIRECTLY")
    print("=" * 60)
    
    try:
        from courtlistener_integration import search_citation
        
        citation = "146 Wn.2d 1, 9, 43 P.3d 4"
        print(f"Testing citation: {citation}")
        
        found, data = search_citation(citation)
        
        if found and data:
            print("✅ Citation found in CourtListener")
            print(f"Case Name: {data.get('caseName', 'N/A')}")
            print(f"Date Filed: {data.get('dateFiled', 'N/A')}")
            print(f"URL: {data.get('absolute_url', 'N/A')}")
            
            case_name = data.get('caseName', '')
            if case_name == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                print("✅ CORRECT CASE NAME FOUND!")
                return True
            else:
                print(f"❌ WRONG CASE NAME: {case_name}")
                return False
        else:
            print("❌ Citation not found in CourtListener")
            return False
            
    except Exception as e:
        print(f"❌ CourtListener test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_citation_lookup_direct():
    """Test citation lookup directly with the debug script."""
    print("\nTESTING CITATION LOOKUP DIRECTLY")
    print("=" * 60)
    
    try:
        # Use the debug script we created earlier
        from debug_citation_collision import test_citation_lookup
        
        citation = "146 Wn.2d 1, 9, 43 P.3d 4"
        print(f"Testing citation: {citation}")
        
        # Import the function and test it
        import os
        import requests
        
        api_key = os.environ.get('COURTLISTENER_API_KEY')
        if not api_key:
            print("❌ No CourtListener API key found")
            return False
        
        headers = {"Authorization": f"Token {api_key}"}
        
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        data = {"text": citation}
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                citation_data = data[0]
                clusters = citation_data.get('clusters', [])
                
                if clusters:
                    cluster = clusters[0]
                    case_name = cluster.get('case_name', '')
                    print(f"✅ Citation found in CourtListener")
                    print(f"Case Name: {case_name}")
                    
                    if case_name == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                        print("✅ CORRECT CASE NAME FOUND!")
                        return True
                    else:
                        print(f"❌ WRONG CASE NAME: {case_name}")
                        return False
                else:
                    print("❌ No clusters found")
                    return False
            else:
                print("❌ No data returned")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Citation lookup test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("DIRECT CITATION PROCESSING TEST")
    print("=" * 60)
    
    # Test direct processing
    processing_success = test_direct_processing()
    
    # Test CourtListener directly
    courtlistener_success = test_courtlistener_direct()
    
    # Test citation lookup directly
    lookup_success = test_citation_lookup_direct()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Direct Processing: {'✅ PASSED' if processing_success else '❌ FAILED'}")
    print(f"CourtListener API: {'✅ PASSED' if courtlistener_success else '❌ FAILED'}")
    print(f"Citation Lookup: {'✅ PASSED' if lookup_success else '❌ FAILED'}")
    
    if processing_success and courtlistener_success and lookup_success:
        print("\n🎉 All tests passed! The issue is likely in the API layer or caching.")
    else:
        print("\n⚠ Some tests failed. The issue is in the processing logic.")

if __name__ == "__main__":
    main() 