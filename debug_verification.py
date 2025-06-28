#!/usr/bin/env python3
"""
Debug script to test citation verification
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    print("✓ Successfully imported EnhancedMultiSourceVerifier")
    
    verifier = EnhancedMultiSourceVerifier()
    print("✓ Successfully created verifier instance")
    
    # Test a simple citation
    test_citation = "97 Wn.2d 30"
    print(f"Testing citation: {test_citation}")
    
    result = verifier.verify_citation_unified_workflow(test_citation)
    print(f"Result: {result}")
    
    # Test complex citation processing
    from complex_citation_integration import process_text_with_complex_citations
    print("✓ Successfully imported complex citation integration")
    
    complex_results = process_text_with_complex_citations(test_citation, verifier)
    print(f"Complex processing results: {complex_results}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 