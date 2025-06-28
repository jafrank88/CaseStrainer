#!/usr/bin/env python3
"""
Test script to check early stopping optimization functionality.
UPDATED: Now uses the unified workflow instead of deprecated web search methods.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_workflow_performance():
    """Test the unified workflow performance and early stopping."""
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test citations with varying complexity
        test_citations = [
            "347 U.S. 483",           # Should be fast (CourtListener)
            "410 U.S. 113",           # Should be fast (CourtListener)
            "384 U.S. 436",           # Should be fast (CourtListener)
            "181 Wash. 2d 401",       # May be slower (web search)
            "State v. Smith",         # May be slower (web search)
            "95 L.Ed.2d 1",           # Should be fast (CourtListener)
            "74 S.Ct. 686"            # Should be fast (CourtListener)
        ]
        
        print(f"Testing unified workflow performance...")
        print("=" * 60)
        
        total_time = 0
        successful_verifications = 0
        
        for citation in test_citations:
            print(f"\nTesting: {citation}")
            print("-" * 40)
            
            start_time = time.time()
            
            try:
                # Use the unified workflow
                result = verifier.verify_citation_unified_workflow(citation)
                
                end_time = time.time()
                duration = end_time - start_time
                total_time += duration
                
                print(f"Duration: {duration:.2f} seconds")
                print(f"Verified: {result.get('verified', False)}")
                print(f"Source: {result.get('source', 'Unknown')}")
                print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
                
                if result.get('verified'):
                    successful_verifications += 1
                
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
                    
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                total_time += duration
                print(f"Duration: {duration:.2f} seconds")
                print(f"Error testing {citation}: {e}")
        
        # Performance summary
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total Citations Tested: {len(test_citations)}")
        print(f"Successful Verifications: {successful_verifications}")
        print(f"Success Rate: {(successful_verifications/len(test_citations)*100):.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Citation: {(total_time/len(test_citations)):.2f} seconds")
        print(f"Citations per Minute: {(len(test_citations)/(total_time/60)):.1f}")
        
        # Check if early stopping is working
        if total_time < 60:  # Should complete in under 1 minute
            print("✅ Early stopping optimization working well!")
        else:
            print("⚠️ Performance may need optimization")
        
        print("Unified workflow performance test completed!")
        
    except Exception as e:
        print(f"Error initializing verifier: {e}")

if __name__ == "__main__":
    test_unified_workflow_performance() 