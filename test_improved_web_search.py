#!/usr/bin/env python3
"""
Test script to check improved web search functionality.
UPDATED: Now uses the unified workflow instead of deprecated web search methods.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_workflow_improved():
    """Test the unified workflow with improved functionality."""
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test citations with various complexity levels
        test_citations = [
            "347 U.S. 483",           # Simple US Supreme Court
            "410 U.S. 113",           # Another US Supreme Court
            "384 U.S. 436",           # Miranda case
            "181 Wash. 2d 401",       # State Supreme Court
            "State v. Smith",         # Generic state case
            "95 L.Ed.2d 1",           # Lawyers Edition
            "74 S.Ct. 686",           # Supreme Court Reporter
            "640 P.2d 716 (1982)"     # With year
        ]
        
        print(f"Testing unified workflow with improved functionality...")
        print("=" * 60)
        
        for citation in test_citations:
            print(f"\nTesting: {citation}")
            print("-" * 40)
            
            try:
                # Use the unified workflow
                result = verifier.verify_citation_unified_workflow(citation)
                
                print(f"Verified: {result.get('verified', False)}")
                print(f"Source: {result.get('source', 'Unknown')}")
                print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                print(f"Court: {result.get('court', 'N/A')}")
                print(f"Date: {result.get('canonical_date', 'N/A')}")
                print(f"Extracted Date: {result.get('extracted_date', 'N/A')}")
                
                # Check for additional metadata
                if result.get('parallel_citations'):
                    print(f"Parallel Citations: {len(result['parallel_citations'])} found")
                
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
                    
            except Exception as e:
                print(f"Error testing {citation}: {e}")
        
        print("\n" + "=" * 60)
        print("Unified workflow improved test completed!")
        
    except Exception as e:
        print(f"Error initializing verifier: {e}")

if __name__ == "__main__":
    test_unified_workflow_improved() 