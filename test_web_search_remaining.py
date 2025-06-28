#!/usr/bin/env python3
"""
Test script to check remaining web search functionality.
UPDATED: Now uses the unified workflow instead of deprecated web search methods.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_workflow():
    """Test the unified workflow with various citation types."""
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test citations
        test_citations = [
            "347 U.S. 483",
            "410 U.S. 113",
            "384 U.S. 436",
            "95 L.Ed.2d 1",
            "State v. Smith"
        ]
        
        print(f"Testing unified workflow with {len(test_citations)} citations...")
        print("=" * 60)
        
        for citation in test_citations:
            print(f"\nTesting: {citation}")
            print("-" * 40)
            
            try:
                # Use the unified workflow instead of deprecated web search
                result = verifier.verify_citation_unified_workflow(citation)
                
                print(f"Verified: {result.get('verified', False)}")
                print(f"Source: {result.get('source', 'Unknown')}")
                print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
                    
            except Exception as e:
                print(f"Error testing {citation}: {e}")
        
        print("\n" + "=" * 60)
        print("Unified workflow test completed!")
        
    except Exception as e:
        print(f"Error initializing verifier: {e}")

if __name__ == "__main__":
    test_unified_workflow() 