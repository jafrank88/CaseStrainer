#!/usr/bin/env python3
"""
Debug script to investigate canonical case matching and case name extraction issues.
"""

import json
import logging
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_canonical_matching():
    """Test canonical case matching with known problematic citations."""
    
    # Test cases that might have wrong canonical matches
    test_cases = [
        {
            "citation": "200 Wn.2d 72",
            "text": "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).",
            "expected_case": "Convoyant, LLC v. DeepThink, LLC"
        },
        {
            "citation": "146 Wn.2d 1", 
            "text": "We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
            "expected_case": "Dep't of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            "citation": "171 Wn.2d 486",
            "text": "Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).",
            "expected_case": "Carlson v. Glob. Client Sols., LLC"
        }
    ]
    
    processor = UnifiedCitationProcessorV2()
    
    print("=== TESTING CANONICAL CASE MATCHING ===")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected case: {test_case['expected_case']}")
        print(f"Text: {test_case['text']}")
        
        try:
            # Process the citation
            results = processor.process_text(test_case['text'])
            
            # Find our specific citation
            citation_result = None
            for result in results:
                if result.citation == test_case['citation']:
                    citation_result = result
                    break
            
            if citation_result:
                print(f"✓ Citation found in results")
                print(f"  Extracted case name: {citation_result.extracted_case_name}")
                print(f"  Canonical name: {citation_result.canonical_name}")
                print(f"  Canonical date: {citation_result.canonical_date}")
                print(f"  URL: {citation_result.url}")
                print(f"  Verified: {citation_result.verified}")
                print(f"  Source: {citation_result.source}")
                
                # Check if canonical name matches expected
                if citation_result.canonical_name == test_case['expected_case']:
                    print(f"  ✓ Canonical name matches expected")
                else:
                    print(f"  ✗ Canonical name mismatch!")
                    print(f"    Expected: {test_case['expected_case']}")
                    print(f"    Got: {citation_result.canonical_name}")
            else:
                print(f"✗ Citation not found in results")
                
        except Exception as e:
            print(f"✗ Error processing citation: {e}")

def test_case_name_extraction():
    """Test case name extraction specifically."""
    
    print("\n=== TESTING CASE NAME EXTRACTION ===")
    
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    test_citations = [
        "200 Wn.2d 72",
        "171 Wn.2d 486", 
        "146 Wn.2d 1"
    ]
    
    for citation in test_citations:
        print(f"\n--- Testing extraction for: {citation} ---")
        
        try:
            # Test the comprehensive extraction function
            result = extract_case_name_triple_comprehensive(
                text=test_text,
                citation=citation,
                api_key=None,
                context_window=100
            )
            
            print(f"Extraction result:")
            print(f"  Extracted name: {result.get('extracted_name')}")
            print(f"  Canonical name: {result.get('canonical_name')}")
            print(f"  Case name: {result.get('case_name')}")
            print(f"  Extracted date: {result.get('extracted_date')}")
            print(f"  Canonical date: {result.get('canonical_date')}")
            print(f"  Confidence: {result.get('case_name_confidence')}")
            print(f"  Method: {result.get('case_name_method')}")
            
            # Check debug info
            debug_info = result.get('debug_info', {})
            if debug_info:
                print(f"  Debug info:")
                for key, value in debug_info.items():
                    print(f"    {key}: {value}")
                    
        except Exception as e:
            print(f"✗ Error in extraction: {e}")

def test_verification_logic():
    """Test the verification logic specifically."""
    
    print("\n=== TESTING VERIFICATION LOGIC ===")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test a specific citation that might have wrong canonical data
    citation = "200 Wn.2d 72"
    
    print(f"Testing verification for: {citation}")
    
    try:
        # Test the verification method directly
        verify_result = processor._verify_with_courtlistener_search(
            citation=citation,
            extracted_case_name="Convoyant, LLC v. DeepThink, LLC",
            extracted_date="2022"
        )
        
        print(f"Verification result:")
        print(f"  Verified: {verify_result.get('verified')}")
        print(f"  Canonical name: {verify_result.get('canonical_name')}")
        print(f"  Canonical date: {verify_result.get('canonical_date')}")
        print(f"  URL: {verify_result.get('url')}")
        print(f"  Source: {verify_result.get('source')}")
        
        # Check raw data
        raw_data = verify_result.get('raw')
        if raw_data:
            print(f"  Raw data keys: {list(raw_data.keys())}")
            print(f"  Case name from raw: {raw_data.get('caseName')}")
            print(f"  Court from raw: {raw_data.get('court')}")
            print(f"  Jurisdiction from raw: {raw_data.get('jurisdiction')}")
            
    except Exception as e:
        print(f"✗ Error in verification: {e}")

def test_state_filtering():
    """Test state filtering logic."""
    
    print("\n=== TESTING STATE FILTERING ===")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test state inference
    test_citations = [
        "200 Wn.2d 72",
        "146 Wn.2d 1",
        "171 Wn.2d 486"
    ]
    
    for citation in test_citations:
        try:
            expected_state = processor._infer_state_from_citation(citation)
            print(f"Citation: {citation} -> Expected state: {expected_state}")
        except Exception as e:
            print(f"Error inferring state for {citation}: {e}")

if __name__ == "__main__":
    test_canonical_matching()
    test_case_name_extraction()
    test_verification_logic()
    test_state_filtering() 