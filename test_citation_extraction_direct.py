"""
Direct test of citation extraction functionality
"""

import sys
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_citation_extraction():
    """Test the citation extraction directly"""
    try:
        # Add the src directory to the path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import the citation extractor
        from services.citation_extractor import CitationExtractor
        from models.citation import CitationResult
        
        # Sample text with citations
        test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
        
        logger.info("Testing citation extraction...")
        logger.info(f"Input text length: {len(test_text)} characters")
        
        # Initialize the citation extractor
        extractor = CitationExtractor()
        
        # Extract citations
        logger.info("Extracting citations...")
        citations = extractor.extract_citations(test_text)
        
        # Print results
        print("\n" + "="*80)
        print("CITATION EXTRACTION RESULTS")
        print("="*80)
        
        if citations:
            print(f"\nFound {len(citations)} citations:")
            print("-"*60)
            
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print("-"*40)
                
                # Handle different citation formats
                if hasattr(citation, 'to_dict'):
                    citation_data = citation.to_dict()
                elif isinstance(citation, dict):
                    citation_data = citation
                else:
                    print(f"  [Unsupported citation type: {type(citation).__name__}]")
                    print(f"  {citation}")
                    continue
                
                # Display common citation fields
                for key in ['citation', 'case_name', 'year', 'volume', 'reporter', 'page', 'url']:
                    if key in citation_data and citation_data[key]:
                        print(f"  {key}: {citation_data[key]}")
                
                # Display any metadata
                if 'metadata' in citation_data and citation_data['metadata']:
                    print("  metadata:")
                    for k, v in citation_data['metadata'].items():
                        print(f"    {k}: {v}")
                
                # Display any additional fields
                other_fields = set(citation_data.keys()) - {'citation', 'case_name', 'year', 'volume', 'reporter', 'page', 'url', 'metadata'}
                for field in other_fields:
                    if citation_data[field]:  # Only show non-empty fields
                        print(f"  {field}: {citation_data[field]}")
        else:
            print("\nNo citations found in the text.")
        
        return citations
        
    except Exception as e:
        logger.error(f"Error in test_citation_extraction: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("=== Starting Citation Extraction Test ===")
    try:
        result = test_citation_extraction()
        logger.info("=== Test Completed Successfully ===")
    except Exception as e:
        logger.error("=== Test Failed ===", exc_info=True)
        sys.exit(1)
