#!/usr/bin/env python3
"""
Debug script to test verification logic and case name extraction.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def debug_verification():
    """Debug the verification logic and case name extraction."""
    
    # Test text with Washington citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)."""
    
    print("Testing with verification disabled and low confidence threshold...")
    print("=" * 60)
    
    # Test with verification disabled and low confidence threshold
    config = ProcessingConfig(enable_verification=False, debug_mode=True, min_confidence=0.0)
    processor = UnifiedCitationProcessorV2(config)
    result = processor.process_text(test_text)
    
    print(f"Citations found (verification disabled, min_confidence=0.0): {len(result)}")
    for i, citation in enumerate(result, 1):
        print(f"Citation {i}:")
        print(f"  Text: {citation.citation}")
        print(f"  Confidence: {citation.confidence}")
        print(f"  Extracted Case Name: {citation.extracted_case_name}")
        print(f"  Extracted Date: {citation.extracted_date}")
        print(f"  Method: {citation.method}")
        print(f"  Is Parallel: {citation.is_parallel}")
        print(f"  Parallel Citations: {citation.parallel_citations}")
        print()
    
    print("Testing with verification enabled and low confidence threshold...")
    print("=" * 60)
    
    # Test with verification enabled and low confidence threshold
    config = ProcessingConfig(enable_verification=True, debug_mode=True, min_confidence=0.0)
    processor = UnifiedCitationProcessorV2(config)
    result = processor.process_text(test_text)
    
    print(f"Citations found (verification enabled, min_confidence=0.0): {len(result)}")
    for i, citation in enumerate(result, 1):
        print(f"Citation {i}:")
        print(f"  Text: {citation.citation}")
        print(f"  Confidence: {citation.confidence}")
        print(f"  Verified: {citation.verified}")
        print(f"  Canonical Name: {citation.canonical_name}")
        print(f"  Canonical Date: {citation.canonical_date}")
        print(f"  URL: {citation.url}")
        print(f"  Extracted Case Name: {citation.extracted_case_name}")
        print(f"  Extracted Date: {citation.extracted_date}")
        print(f"  Method: {citation.method}")
        print(f"  Is Parallel: {citation.is_parallel}")
        print(f"  Parallel Citations: {citation.parallel_citations}")
        print()

# Test semicolon boundary detection
print("\n" + "="*60)
print("Testing semicolon boundary detection...")
print("="*60)

test_text_with_semicolons = """
The court held that the statute was constitutional. Smith v. State, 123 Wash. 2d 456, 789 P.2d 123 (1990); 
Jones v. County, 456 Wash. 2d 789, 123 P.2d 456 (1991); and Brown v. City, 789 Wash. 2d 123, 456 P.2d 789 (1992). 
The legislature later amended the statute.
"""

config = ProcessingConfig(
    use_eyecite=False,
    use_regex=True,
    extract_case_names=True,
    extract_dates=True,
    enable_clustering=True,
    enable_deduplication=True,
    enable_verification=False,
    context_window=300,
    min_confidence=0.0,
    debug_mode=True
)

processor = UnifiedCitationProcessorV2(config)
citations = processor.process_text(test_text_with_semicolons)

print(f"\nCitations found with semicolon boundaries: {len(citations)}")
for i, citation in enumerate(citations, 1):
    print(f"Citation {i}:")
    print(f"  Text: {citation.citation}")
    print(f"  Extracted Case Name: {citation.extracted_case_name}")
    print(f"  Extracted Date: {citation.extracted_date}")
    print(f"  Context: '{citation.context[:100]}...'")
    print()

if __name__ == "__main__":
    debug_verification() 