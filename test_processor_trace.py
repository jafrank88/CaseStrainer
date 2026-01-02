"""
Trace through the processor to find where extraction diverges from direct extraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging

# Enable debug logging
logging.basicConfig(level=logging.WARNING)

TEXT = """In Smith v. Jones, 500 U.S. 123 (1991), the Supreme Court held that federal courts have jurisdiction over such matters. This principle was reaffirmed in Johnson v. Texas, 509 U.S. 350 (1993), where the Court emphasized the importance of due process."""

async def test_processor():
    """Test the processor and trace extraction."""
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    processor = UnifiedCitationProcessorV2()
    
    # Step 1: Extract with eyecite
    print("=" * 60)
    print("STEP 1: Eyecite extraction")
    print("=" * 60)
    
    citations = processor._extract_with_eyecite(TEXT)
    print(f"Eyecite found {len(citations)} citations")
    
    for c in citations:
        print(f"\nCitation: {c.citation}")
        print(f"  Position: {c.start_index}-{c.end_index}")
        print(f"  extracted_case_name (before _extract_metadata): {getattr(c, 'extracted_case_name', 'NOT SET')}")
    
    # Step 2: Call _extract_metadata for each citation
    print("\n" + "=" * 60)
    print("STEP 2: Call _extract_metadata")
    print("=" * 60)
    
    for c in citations:
        print(f"\nProcessing {c.citation}...")
        processor._extract_metadata(c, TEXT, None)
        print(f"  extracted_case_name (after _extract_metadata): {getattr(c, 'extracted_case_name', 'NOT SET')}")
    
    # Step 3: Check final results
    print("\n" + "=" * 60)
    print("STEP 3: Final Results")
    print("=" * 60)
    
    for c in citations:
        print(f"{c.citation}: {getattr(c, 'extracted_case_name', 'N/A')}")
    
    return citations

if __name__ == "__main__":
    asyncio.run(test_processor())
