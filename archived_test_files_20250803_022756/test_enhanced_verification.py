#!/usr/bin/env python3
"""
Test the enhanced verification features integrated into the main pipeline
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_enhanced_verification():
    """Test the enhanced verification features with validation and better error reporting."""
    
    # Create processor with verification and debug mode enabled
    config = ProcessingConfig(
        enable_verification=True,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Test text with a mix of good and potentially problematic citations
    test_text = """
    The Supreme Court in Garrity v. New Jersey, 385 U.S. 493 (1967), established important precedent.
    See also Davis v. Alaska, 94 S. Ct. 1105, 39 L. Ed. 2d 347 (1974).
    Compare with Terry v. Ohio, 392 U.S. 1, 88 S. Ct. 1868 (1968).
    But see 2021 WL 1234567 (unpublished case).
    """
    
    print("Testing Enhanced CaseStrainer Verification Pipeline")
    print("=" * 60)
    print(f"Test text: {test_text.strip()}")
    print("=" * 60)
    
    # Process the text
    results = processor.process_text(test_text)
    
    print(f"\n=== PROCESSING RESULTS ===")
    print(f"Found {len(results['citations'])} citations")
    print(f"Created {len(results['clusters'])} clusters")
    print()
    
    # Examine each citation with enhanced reporting
    verified_count = 0
    high_confidence_count = 0
    validation_passed_count = 0
    
    for i, citation in enumerate(results['citations'], 1):
        print(f"Citation #{i}: {citation.citation}")
        print(f"  Verified: {citation.verified}")
        
        if citation.verified:
            verified_count += 1
            print(f"  ✓ Canonical name: {citation.canonical_name}")
            print(f"  ✓ Canonical date: {citation.canonical_date}")
            print(f"  ✓ Source: {citation.source}")
            print(f"  ✓ URL: {citation.url}")
            
            if hasattr(citation, 'confidence') and citation.confidence:
                print(f"  ✓ Confidence: {citation.confidence:.2f}")
                if citation.confidence > 0.8:
                    high_confidence_count += 1
            
            if hasattr(citation, 'metadata') and citation.metadata:
                if citation.metadata.get('validation_passed'):
                    validation_passed_count += 1
                    print(f"  ✓ Validation: PASSED")
                print(f"  ✓ Verification method: {citation.metadata.get('verification_method', 'unknown')}")
                if 'fallback_source' in citation.metadata:
                    print(f"  ✓ Fallback source: {citation.metadata['fallback_source']}")
        else:
            print(f"  ✗ Not verified")
            
        print(f"  Extracted name: {getattr(citation, 'extracted_case_name', 'N/A')}")
        print(f"  Extracted date: {getattr(citation, 'extracted_date', 'N/A')}")
        print()
    
    # Summary statistics
    print("=== ENHANCED VERIFICATION SUMMARY ===")
    print(f"Total citations: {len(results['citations'])}")
    print(f"Verified citations: {verified_count}")
    print(f"Verification rate: {(verified_count/len(results['citations']))*100:.1f}%")
    print(f"High confidence (>0.8): {high_confidence_count}")
    print(f"Validation passed: {validation_passed_count}")
    print()
    
    # Test specific enhancements
    print("=== TESTING ENHANCED FEATURES ===")
    
    # Check if we have proper validation
    if validation_passed_count > 0:
        print("✓ Verification result validation is working")
    else:
        print("⚠ No validation metadata found")
    
    # Check if we have confidence scores
    confidence_citations = [c for c in results['citations'] if c.verified and hasattr(c, 'confidence') and c.confidence]
    if confidence_citations:
        avg_confidence = sum(c.confidence for c in confidence_citations) / len(confidence_citations)
        print(f"✓ Confidence scoring is working (avg: {avg_confidence:.2f})")
    else:
        print("⚠ No confidence scores found")
    
    # Check if we have enhanced metadata
    metadata_citations = [c for c in results['citations'] if c.verified and hasattr(c, 'metadata') and c.metadata]
    if metadata_citations:
        print("✓ Enhanced metadata is working")
    else:
        print("⚠ No enhanced metadata found")
    
    print()
    print("Enhanced verification test completed!")
    
    return results

if __name__ == "__main__":
    test_enhanced_verification()
