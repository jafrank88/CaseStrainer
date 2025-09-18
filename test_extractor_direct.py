import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the extractor
try:
    from citation_extractor import CitationExtractor
    logger.info("Successfully imported CitationExtractor")
except Exception as e:
    logger.error(f"Failed to import CitationExtractor: {e}")
    raise

def test_extraction():
    try:
        extractor = CitationExtractor()
        logger.info("Created CitationExtractor instance")
        
        # Test case with WL citation
        text = "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)"
        logger.info(f"Testing text: {text}")
        
        # Extract citations
        citations = extractor.extract_citations(text)
        logger.info(f"Extracted {len(citations)} citations")
        
        # Print citations
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Text: {citation.citation}")
            print(f"  Type: {type(citation).__name__}")
            print(f"  Metadata: {citation.metadata}")
            
            # Check if this is a WL citation
            if "WL" in citation.citation:
                print("  This is a WL citation")
                # The citation should be in the format "2006 WL 3801910"
                parts = citation.citation.split()
                if len(parts) >= 3 and parts[1] == "WL":
                    print(f"  - Year: {parts[0]}")
                    print(f"  - Document number: {parts[2]}")
                    return True
        
        print("No WL citation found in the expected format")
        return False
    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("Testing WL citation extraction...")
    success = test_extraction()
    
    if success:
        print("\nTest passed!")
    else:
        print("\nTest failed.")
        sys.exit(1)
