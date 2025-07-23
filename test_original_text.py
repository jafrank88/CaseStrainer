#!/usr/bin/env python3
"""
Test script to verify the original text with all citations
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_original_text():
    """Test the original text with all citations"""
    
    print("=== Testing Original Text ===")
    
    # The original text from the user's output
    test_text = """We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"""
    
    print(f"Text length: {len(test_text)} characters")
    print(f"Text preview: {test_text[:100]}...")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        
        print(f"\nProcessing text...")
        results = processor.process_text(test_text)
        
        print(f"\nProcessing completed")
        print(f"Citations found: {len(results.get('citations', []))}")
        print(f"Clusters found: {len(results.get('clusters', []))}")
        
        print(f"\n=== CITATIONS ===")
        for i, citation in enumerate(results.get('citations', []), 1):
            print(f"\n{i}. Citation: {citation.citation}")
            print(f"   Verified: {citation.verified}")
            print(f"   Source: {citation.source}")
            print(f"   Extracted case name: {citation.extracted_case_name}")
            print(f"   Canonical name: {citation.canonical_name}")
            print(f"   Extracted date: {citation.extracted_date}")
            print(f"   Canonical date: {citation.canonical_date}")
            print(f"   URL: {citation.url}")
            print(f"   Method: {citation.method}")
            print(f"   Pattern: {citation.pattern}")
            print(f"   Context: {citation.context[:100]}...")
        
        print(f"\n=== CLUSTERS ===")
        for i, cluster in enumerate(results.get('clusters', []), 1):
            print(f"\n{i}. Cluster: {cluster.get('cluster_id', 'Unknown')}")
            print(f"   Canonical name: {cluster.get('canonical_name')}")
            print(f"   Canonical date: {cluster.get('canonical_date')}")
            print(f"   Extracted name: {cluster.get('extracted_case_name')}")
            print(f"   Extracted date: {cluster.get('extracted_date')}")
            print(f"   Size: {cluster.get('size', 0)}")
            print(f"   Source: {cluster.get('source')}")
            print(f"   Citations:")
            for j, cluster_citation in enumerate(cluster.get('citations', []), 1):
                print(f"     {j}. {cluster_citation.get('citation')} - Verified: {cluster_citation.get('verified')}")
        
        # Summary
        verified_count = len([c for c in results.get('citations', []) if c.verified])
        total_count = len(results.get('citations', []))
        print(f"\n=== SUMMARY ===")
        print(f"Total citations: {total_count}")
        print(f"Verified citations: {verified_count}")
        print(f"Verification rate: {verified_count/total_count*100:.1f}%" if total_count > 0 else "N/A")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_original_text() 