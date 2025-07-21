#!/usr/bin/env python3
"""
Test script to verify CourtListener fallback to comprehensive web search engine.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_courtlistener_fallback():
    """Test that citations not found in CourtListener fall back to web search."""
    
    # Test citations - some should be found in CourtListener, others should fall back
    test_citations = [
        "410 U.S. 113",  # Should be found in CourtListener (Roe v. Wade)
        "347 U.S. 483",  # Should be found in CourtListener (Brown v. Board)
        "200 Wn.2d 72",  # Washington case - might need fallback
        "171 Wn.2d 486", # Washington case - might need fallback
        "999 U.S. 999",  # Fake citation - should trigger fallback
        "123 Fake. 456", # Completely fake - should trigger fallback
    ]
    
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    print("=" * 80)
    print("TESTING COURTLISTENER FALLBACK TO COMPREHENSIVE WEB SEARCH")
    print("=" * 80)
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        try:
            # Test the unified workflow
            result = processor.verify_citation_unified_workflow(citation)
            
            print(f"Result:")
            print(f"  Verified: {result.get('verified', False)}")
            print(f"  Verified by: {result.get('verified_by', 'None')}")
            print(f"  Case name: {result.get('canonical_name', 'None')}")
            print(f"  Date: {result.get('canonical_date', 'None')}")
            print(f"  URL: {result.get('url', 'None')}")
            print(f"  Confidence: {result.get('confidence', 0.0)}")
            
            # Check sources
            sources = result.get('sources', {})
            if 'courtlistener' in sources:
                cl_result = sources['courtlistener']
                print(f"  CourtListener result: {cl_result.get('verified', False)}")
            
            if 'legal_websearch' in sources:
                web_result = sources['legal_websearch']
                print(f"  Web search result: {web_result.get('reliability_score', 0)}")
            
            # Verify fallback behavior
            if result.get('verified'):
                if result.get('verified_by') == 'CourtListener':
                    print(f"  ✓ Found in CourtListener")
                elif result.get('verified_by') == 'Legal Websearch':
                    print(f"  ✓ Found via web search fallback")
                else:
                    print(f"  ✓ Found via {result.get('verified_by')}")
            else:
                print(f"  ✗ Not verified by any source")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

def test_batch_processing():
    """Test batch processing with multiple citations."""
    
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    Some landmark cases include Roe v. Wade, 410 U.S. 113 (1973), and Brown v. Board of Education, 347 U.S. 483 (1954).
    
    This fake citation should trigger fallback: 999 U.S. 999 (1999).
    """
    
    print(f"\n{'='*80}")
    print("TESTING BATCH PROCESSING WITH FALLBACK")
    print(f"{'='*80}")
    
    processor = UnifiedCitationProcessorV2()
    
    try:
        # Process the text
        citations = processor.process_text(test_text)
        
        print(f"Found {len(citations)} citations:")
        
        for i, citation in enumerate(citations, 1):
            print(f"\n{i}. Citation: {citation.citation}")
            print(f"   Verified: {citation.verified}")
            print(f"   Source: {citation.source}")
            print(f"   Case name: {citation.canonical_name}")
            print(f"   Date: {citation.canonical_date}")
            print(f"   URL: {citation.url}")
            
            # Check if it was verified by CourtListener or fallback
            if citation.verified:
                if citation.source == "CourtListener":
                    print(f"   ✓ Found in CourtListener")
                elif "Websearch" in citation.source or "Legal" in citation.source:
                    print(f"   ✓ Found via web search fallback")
                else:
                    print(f"   ✓ Found via {citation.source}")
            else:
                print(f"   ✗ Not verified")
                
    except Exception as e:
        print(f"Error in batch processing: {e}")

if __name__ == "__main__":
    print("Starting CourtListener fallback tests...")
    
    # Test individual citations
    asyncio.run(test_courtlistener_fallback())
    
    # Test batch processing
    test_batch_processing()
    
    print("\nAll tests completed!") 