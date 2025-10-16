import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

# Set up basic logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import only what we need
try:
    from citation_extractor import CitationExtractor
    logger.info("Successfully imported CitationExtractor")
    
    # Create a minimal extractor with just the WL pattern
    extractor = CitationExtractor()
    
    # Test text with WL citation
    test_text = "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)"
    print(f"Testing text: {test_text}")
    
    # Try to extract citations
    try:
        citations = extractor.extract_citations(test_text)
        print(f"Found {len(citations)} citations")
        
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Text: {citation.citation}")
            
            # Check if this is a WL citation
            if "WL" in citation.citation:
                print("  This is a WL citation")
                # The citation should be in the format "2006 WL 3801910"
                parts = citation.citation.split()
                if len(parts) >= 3 and parts[1] == "WL":
                    print(f"  - Year: {parts[0]}")
                    print(f"  - Document number: {parts[2]}")
                    print("\nTest passed!")
                    sys.exit(0)
        
        print("\nNo WL citation found in the expected format")
        
    except Exception as e:
        print(f"\nError during extraction: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"\nFailed to import or use CitationExtractor: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

sys.exit(1)
