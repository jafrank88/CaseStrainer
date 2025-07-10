#!/usr/bin/env python3
"""
Test the full backend pipeline to verify that extracted_date fields are properly populated.
"""

import sys
import os
import json
import inspect

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def debug_date_assignment():
    """
    Add date assignment tracer to see exactly where extracted_date gets set.
    """
    from src.unified_citation_processor_v2 import CitationResult
    
    original_setattr = CitationResult.__setattr__

    def debug_setattr(self, name, value):
        if name == 'extracted_date':
            caller_info = inspect.stack()[1]
            current_value = getattr(self, 'extracted_date', 'UNSET')
            citation_text = getattr(self, 'citation', 'UNKNOWN')
            
            print(f"📅 DATE ASSIGNMENT:")
            print(f"   Citation: {citation_text}")
            print(f"   Change: '{current_value}' → '{value}'")
            print(f"   Source: {caller_info.function} at line {caller_info.lineno}")
            print(f"   File: {caller_info.filename.split('/')[-1]}")
            
            if current_value and current_value != 'UNSET' and not value:
                print(f"   ⚠️ WARNING: Overwriting good value with blank!")
            print()
            
        return original_setattr(self, name, value)

    CitationResult.__setattr__ = debug_setattr
    print("🔧 Date assignment tracer installed")

def test_document_only_extraction():
    """
    Test extraction without any API contamination.
    """
    print("\n" + "="*60)
    print("🧪 DOCUMENT-ONLY EXTRACTION TEST")
    print("="*60)
    
    # Sample text with actual citations from your document
    sample_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)."""
    
    # Mock API calls to return None
    def mock_api_call(*args, **kwargs):
        return None
    
    # Temporarily replace API functions
    # DEPRECATED: get_canonical_case_name_with_date functionality moved to UnifiedCitationProcessorV2
    original_api_func = get_canonical_case_name_with_date
    
    try:
        # Replace with mock
        import src.unified_citation_processor as ucp
        ucp.get_canonical_case_name_with_date = mock_api_call
        
        # Process the text
        processor = UnifiedCitationProcessor()
        result = processor.process_text(sample_text)
        
        print("📋 DOCUMENT-ONLY TEST RESULTS:")
        for i, citation in enumerate(result['results'], 1):
            print(f"\nCitation {i}:")
            print(f"  Citation text: {citation['citation']}")
            print(f"  Extracted case name: {citation.get('extracted_case_name', 'MISSING')}")
            print(f"  Extracted date: {citation.get('extracted_date', 'MISSING')}")
            print(f"  Canonical case name: {citation.get('canonical_name', 'MISSING')}")
            print(f"  Canonical date: {citation.get('canonical_date', 'MISSING')}")
            print("-" * 40)
            
    finally:
        # Restore original API function
        ucp.get_canonical_case_name_with_date = original_api_func

def debug_citation_positions():
    """
    Debug where citations are found vs where they should be.
    """
    print("\n" + "="*60)
    print("🔍 CITATION POSITION ANALYSIS")
    print("="*60)
    
    sample_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)."""
    
    # Parser's citations (from your JSON output)
    parser_citations = [
        "200 Wash. 2d 72, 514 P.3d 643",
        "171 Wash. 2d 486 256 P.3d 321", 
        "146 Wash. 2d 1 43 P.3d 4"
    ]
    
    # Actual citations in document
    actual_citations = [
        "200 Wn.2d 72, 73, 514 P.3d 643",
        "171 Wn.2d 486, 493, 256 P.3d 321",
        "146 Wn.2d 1, 9, 43 P.3d 4"
    ]
    
    print("Citation Position Analysis:")
    for i, (parser_cit, actual_cit) in enumerate(zip(parser_citations, actual_citations)):
        parser_pos = sample_text.find(parser_cit)
        actual_pos = sample_text.find(actual_cit)
        
        print(f"\nCitation {i+1}:")
        print(f"  Parser looks for: '{parser_cit}' → Position: {parser_pos}")
        print(f"  Actually in text: '{actual_cit}' → Position: {actual_pos}")
        
        if actual_pos != -1:
            after_text = sample_text[actual_pos + len(actual_cit):actual_pos + len(actual_cit) + 15]
            print(f"  Text after actual: '{after_text}'")
            
            # Test date extraction at actual position
            from src.enhanced_extraction_utils import extract_case_info_enhanced_with_position
            extraction_result = extract_case_info_enhanced_with_position(
                sample_text, actual_pos, actual_pos + len(actual_cit)
            )
            print(f"  Date extraction result: {extraction_result.get('date', 'MISSING')}")
            print(f"  Case name extraction result: {extraction_result.get('case_name', 'MISSING')}")

def test_date_extraction_isolation():
    """
    Test date extraction with the actual citations from your document.
    """
    print("\n" + "="*60)
    print("🧪 DATE EXTRACTION ISOLATION TEST")
    print("="*60)
    
    # Test with the REAL citations from your document
    test_citations = [
        "200 Wn.2d 72, 73, 514 P.3d 643",  # Not "200 Wash. 2d 72, 514 P.3d 643"
        "171 Wn.2d 486, 493, 256 P.3d 321",  # Not "171 Wash. 2d 486 256 P.3d 321"  
        "146 Wn.2d 1, 9, 43 P.3d 4"  # Not "146 Wash. 2d 1 43 P.3d 4"
    ]

    sample_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)."""

    for citation in test_citations:
        citation_index = sample_text.find(citation)
        if citation_index != -1:
            after_citation = sample_text[citation_index + len(citation):citation_index + len(citation) + 20]
            print(f"Citation: {citation}")
            print(f"Found at index: {citation_index}")
            print(f"Text after: '{after_citation}'")
            
            # Test enhanced extraction
            from src.enhanced_extraction_utils import extract_case_info_enhanced_with_position
            extracted_result = extract_case_info_enhanced_with_position(
                sample_text, citation_index, citation_index + len(citation)
            )
            print(f"Extracted date: {extracted_result.get('date', 'MISSING')}")
            print(f"Extracted case name: {extracted_result.get('case_name', 'MISSING')}")
            print(f"Confidence: {extracted_result.get('overall_confidence', 'MISSING')}")
            print("-" * 50)
        else:
            print(f"❌ Citation not found: {citation}")

def verify_crosscontamination():
    """
    Verify if extracted_case_name is coming from document or API.
    """
    print("\n" + "="*60)
    print("🔍 CROSSCONTAMINATION VERIFICATION")
    print("="*60)
    
    # Add debug prints to the verification process
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    
    class DebugProcessor(UnifiedCitationProcessor):
        def verify_citation(self, citation_text):
            print(f"\n🔍 BEFORE API: extracted_case_name = '{getattr(self, 'extracted_case_name', 'NOT_SET')}'")
            
            # Call original method
            result = super().verify_citation(citation_text)
            
            print(f"🔍 AFTER API: extracted_case_name = '{getattr(self, 'extracted_case_name', 'NOT_SET')}'")
            print(f"🔍 AFTER API: canonical_name = '{getattr(self, 'canonical_name', 'NOT_SET')}'")
            
            return result
    
    # Test with sample text
    sample_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."""
    
    processor = DebugProcessor()
    result = processor.process_text(sample_text)
    
    print("\n📋 CROSSCONTAMINATION TEST RESULTS:")
    for citation in result['results']:
        print(f"Citation: {citation['citation']}")
        print(f"Extracted case name: {citation.get('extracted_case_name', 'MISSING')}")
        print(f"Canonical case name: {citation.get('canonical_name', 'MISSING')}")
        print(f"Are they identical? {citation.get('extracted_case_name') == citation.get('canonical_name')}")
        print("-" * 40)

def test_full_pipeline():
    """Test the complete backend pipeline with date extraction."""
    
    print("=== TESTING FULL BACKEND PIPELINE ===")
    print()
    
    # Sample legal document text
    test_text = """
    The Washington Supreme Court in State v. Smith, 171 Wash. 2d 486 (2011), 
    addressed the issue of search and seizure. The court decided this case on 
    May 12, 2011. This decision was later cited in State v. Johnson, 200 Wash. 2d 72 (2023).
    
    In another case, Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
    held that separate educational facilities are inherently unequal.
    
    The Pacific Reporter citation is 514 P.3d 643 (2023).
    """
    
    print(f"Test document text:")
    print(f"'{test_text.strip()}'")
    print()
    
    # Initialize the processor
    processor = UnifiedCitationProcessor()
    
    # Process the text through the full pipeline
    print("Processing through full pipeline...")
    result = processor.process_text(test_text, {
        'extract_case_names': True,
        'use_enhanced': True,
        'cleaning_steps': ['whitespace', 'quotes', 'unicode']
    })
    
    # Display results
    print(f"\n=== PIPELINE RESULTS ===")
    print(f"Total citations found: {len(result.get('results', []))}")
    print(f"Processing time: {result.get('metadata', {}).get('processing_time', 0):.2f}s")
    print()
    
    # Check each citation result
    for i, citation in enumerate(result.get('results', []), 1):
        print(f"Citation {i}:")
        print(f"  Citation text: {citation.get('citation', 'N/A')}")
        print(f"  Extracted date: '{citation.get('extracted_date', 'N/A')}'")
        print(f"  Canonical date: '{citation.get('canonical_date', 'N/A')}'")
        print(f"  Extracted case name: '{citation.get('extracted_case_name', 'N/A')}'")
        print(f"  Canonical name: '{citation.get('canonical_name', 'N/A')}'")
        print(f"  Verified: {citation.get('verified', False)}")
        print(f"  Method: {citation.get('method', 'N/A')}")
        print(f"  Pattern: {citation.get('pattern', 'N/A')}")
            print()
        
    # Check if extracted_date fields are populated
    citations_with_dates = [c for c in result.get('results', []) if c.get('extracted_date') and c.get('extracted_date') != 'N/A']
    print(f"Citations with extracted dates: {len(citations_with_dates)}/{len(result.get('results', []))}")
    
    if citations_with_dates:
        print("✅ SUCCESS: extracted_date fields are being populated!")
        for citation in citations_with_dates:
            print(f"  - {citation.get('citation')}: {citation.get('extracted_date')}")
    else:
        print("❌ ISSUE: No extracted_date fields are populated")
    
    print()
    
    # Save results to file for inspection
    output_file = "pipeline_test_results.json"
    # Convert CitationStatistics to dict if present
    if 'statistics' in result and hasattr(result['statistics'], '__dict__'):
        result['statistics'] = dict(result['statistics'].__dict__)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    print(f"Full results saved to: {output_file}")
        
        return result
        
def test_specific_citation():
    """Test a specific citation to see the extraction process."""
    
    print("=== TESTING SPECIFIC CITATION EXTRACTION ===")
    print()
    
    test_text = "In State v. Smith, 171 Wash. 2d 486 (2011), the court held..."
    citation = "171 Wash. 2d 486"
    
    print(f"Text: {test_text}")
    print(f"Citation: {citation}")
    print()
    
    # Test the extraction directly
    from src.enhanced_extraction_utils import extract_case_info_enhanced_with_position
    
    # Find the citation position
    start_pos = test_text.find(citation)
    end_pos = start_pos + len(citation)
    
    print(f"Citation position: {start_pos}-{end_pos}")
    print()
    
    # Test with position-based extraction
    result = extract_case_info_enhanced_with_position(test_text, start_pos, end_pos)
    print(f"Position-based extraction result: {result}")
    print()
    
    # Test with string-based extraction
    from src.enhanced_extraction_utils import extract_case_info_enhanced
    result2 = extract_case_info_enhanced(test_text, citation)
    print(f"String-based extraction result: {result2}")
    print()

def test_original_sample_with_fixes():
    sample_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)."""
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    processor = UnifiedCitationProcessor()
    result = processor.process_text(sample_text)
    print("\n🧪 ORIGINAL SAMPLE TEST RESULTS:")
    for citation in result['results']:
        print(f"Citation: {citation['citation']}")
        print(f"Extracted date: {citation.get('extracted_date', 'MISSING')}")
        print(f"Extracted case name: {citation.get('extracted_case_name', 'MISSING')}")
        print("-" * 40)

if __name__ == "__main__":
    print("🔧 Installing debugging tools...")
    debug_date_assignment()
    
    print("\n" + "="*60)
    print("🚀 RUNNING FOCUSED DEBUGGING TESTS")
    print("="*60)
    
    # Run focused debugging tests
    print("\n1. Testing date extraction isolation...")
    test_date_extraction_isolation()
    
    print("\n2. Testing citation position analysis...")
    debug_citation_positions()
    
    print("\n3. Testing document-only extraction...")
    try:
        test_document_only_extraction()
    except Exception as e:
        print(f"Document-only test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ FOCUSED DEBUGGING TESTS COMPLETE")
    print("="*60)
    
    # Run the original tests
    test_specific_citation()
    print("\n" + "="*80 + "\n")
    test_full_pipeline() 
    print("\n4. Testing original sample with all fixes...")
    test_original_sample_with_fixes() 