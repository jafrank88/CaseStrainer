#!/usr/bin/env python3
"""
Test script to verify the new search sources are working correctly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

async def test_new_sources():
    """Test the new search sources."""
    print("Testing new search sources...")
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations
    test_citations = [
        "200 Wash. 2d 72, 514 P.3d 643",  # Washington case
        "410 U.S. 113",  # US Supreme Court case
        "347 U.S. 483"   # Brown v. Board of Education
    ]
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        try:
            # Test the enhanced verification
            result = verifier.verify_citation_unified_workflow(citation)
            
            print(f"Verification result:")
            print(f"  Verified: {result.get('verified', 'unknown')}")
            print(f"  Source: {result.get('source', 'unknown')}")
            print(f"  Method: {result.get('verification_method', 'unknown')}")
            print(f"  URL: {result.get('url', 'none')}")
            print(f"  Confidence: {result.get('confidence', 'unknown')}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
                
        except Exception as e:
            print(f"Error testing {citation}: {e}")
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_new_sources()) 