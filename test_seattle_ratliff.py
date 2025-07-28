#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test City of Seattle v. Ratliff citation with CourtListener API verification.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_seattle_ratliff_citation():
    """Test the City of Seattle v. Ratliff citation for canonical name and date."""
    
    print("City of Seattle v. Ratliff Citation Test")
    print("=" * 45)
    
    try:
        from models import ProcessingConfig
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        print("✅ Successfully imported citation processor")
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            enable_verification=True,
            debug_mode=True,
            use_eyecite=True,
            enable_clustering=True
        )
        
        processor = UnifiedCitationProcessorV2(config)
        print("✅ Successfully initialized citation processor")
        
        # Check if API key is available
        api_key_available = bool(processor.courtlistener_api_key)
        print(f"CourtListener API key available: {api_key_available}")
        if processor.courtlistener_api_key:
            print(f"API key starts with: {processor.courtlistener_api_key[:8]}...")
        
        # Test text containing the City of Seattle v. Ratliff citation
        test_text = """
        The Washington Supreme Court has declared that the right to counsel is of 
        "paramount importance to all persons appearing in our courts." City of Seattle v. Ratliff, 
        100 Wn.2d 212, 218, 667 P.2d 630 (1983). This landmark decision established 
        important precedent for criminal defense rights in Washington State.
        """
        
        print(f"\nTesting with text containing City of Seattle v. Ratliff citation...")
        print("Expected citations:")
        print("- 100 Wn.2d 212")
        print("- 667 P.2d 630")
        print("Expected canonical name: City of Seattle v. Ratliff")
        print("Expected canonical date: 1983")
        
        # Process the text
        print("\n" + "-" * 50)
        print("PROCESSING TEXT...")
        print("-" * 50)
        
        result = processor.process_document_citations(test_text)
        
        print(f"\nRESULTS:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Success: {result.get('success', False)}")
        print(f"Total citations found: {len(result.get('citations', []))}")
        
        # Look for the specific citations
        citations = result.get('citations', [])
        seattle_citations = []
        
        for citation in citations:
            citation_text = citation.get('citation', '')
            if '100 Wn.2d' in citation_text or '667 P.2d' in citation_text:
                seattle_citations.append(citation)
        
        if seattle_citations:
            print(f"\nFound {len(seattle_citations)} City of Seattle v. Ratliff citations:")
            
            for i, citation in enumerate(seattle_citations):
                print(f"\n  Citation {i+1}: {citation.get('citation')}")
                print(f"    Extracted case name: {citation.get('extracted_case_name', 'None')}")
                print(f"    Extracted date: {citation.get('extracted_date', 'None')}")
                print(f"    Canonical name: {citation.get('canonical_name', 'None')}")
                print(f"    Canonical date: {citation.get('canonical_date', 'None')}")
                print(f"    Verified: {citation.get('verified', False)}")
                print(f"    Source: {citation.get('source', 'None')}")
                
                # Check if verification worked
                if citation.get('canonical_name') and citation.get('canonical_date'):
                    print(f"    ✅ CANONICAL DATA FOUND!")
                else:
                    print(f"    ❌ No canonical data (verification may have failed)")
        else:
            print("\n❌ No City of Seattle v. Ratliff citations found")
            print("Available citations:")
            for citation in citations[:5]:  # Show first 5
                print(f"  - {citation.get('citation', 'N/A')}")
        
        # Test the verification directly
        print("\n" + "-" * 50)
        print("DIRECT VERIFICATION TEST")
        print("-" * 50)
        
        try:
            from courtlistener_verification import verify_with_courtlistener
            
            # Test direct verification of the citation
            test_citation = "100 Wn.2d 212"
            extracted_case_name = "City of Seattle v. Ratliff"
            
            print(f"Testing direct verification of: {test_citation}")
            print(f"With extracted case name: {extracted_case_name}")
            
            verify_result = verify_with_courtlistener(
                processor.courtlistener_api_key, 
                test_citation, 
                extracted_case_name
            )
            
            print(f"Verification result: {verify_result}")
            
            if verify_result.get('verified'):
                print("✅ Direct verification successful!")
                print(f"  Canonical name: {verify_result.get('canonical_name')}")
                print(f"  Canonical date: {verify_result.get('canonical_date')}")
            else:
                print("❌ Direct verification failed")
                
        except Exception as e:
            print(f"❌ Direct verification test failed: {e}")
        
        return len(seattle_citations) > 0
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing City of Seattle v. Ratliff with CourtListener API")
    print("=" * 60)
    
    success = test_seattle_ratliff_citation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed - check results above for canonical data!")
    else:
        print("⚠️  Test had issues - check error messages above.")
    
    print("\nThis test verifies:")
    print("1. Citation extraction finds the citations")
    print("2. CourtListener API verification runs with your API key")
    print("3. Canonical name and date are populated")
    print("4. Verification status is correctly set")
