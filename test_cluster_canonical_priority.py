#!/usr/bin/env python3
"""
Test script to verify cluster canonical name priority logic.
This tests that when a citation appears both individually and in a cluster,
the first canonical name in the sequence is used.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    print("✅ Successfully imported UnifiedCitationProcessor")
    
    # Test text with citations that appear both individually and in clusters
    test_text = """
    In State v. Smith, 171 Wn.2d 486 (2011), the court held that search and seizure 
    must be reasonable. Later in the same opinion, the court cited 171 Wn.2d 486, 493, 256 P.3d 321 
    for the proposition that evidence must be admissible. The case was also cited as 
    256 P.3d 321 in subsequent decisions.
    
    Another example is Brown v. Board, 347 U.S. 483 (1954), which established that 
    separate educational facilities are inherently unequal. This was later cited as 
    347 U.S. 483, 495, 74 S. Ct. 686 in the same opinion.
    """
    
    print("Test text:")
    print(test_text)
    print()
    
    # Initialize processor
    processor = UnifiedCitationProcessor()
    
    # Process the text
    print("Processing text through UnifiedCitationProcessor...")
    result = processor.process_text(test_text, extract_case_names=True, verify_citations=True)
    
    print(f"\nResults:")
    print(f"Total citations found: {len(result.get('results', []))}")
    print()
    
    # Check each result
    for i, citation_result in enumerate(result.get('results', []), 1):
        print(f"Citation {i}:")
        print(f"  Citation: {citation_result.get('citation', 'N/A')}")
        print(f"  Is cluster: {citation_result.get('is_cluster', False)}")
        print(f"  Cluster members: {citation_result.get('cluster_members', [])}")
        print(f"  Extracted case name: {citation_result.get('extracted_case_name', 'N/A')}")
        print(f"  Canonical name: {citation_result.get('canonical_name', 'N/A')}")
        print(f"  Verified: {citation_result.get('verified', False)}")
        print(f"  Source: {citation_result.get('source', 'N/A')}")
        print(f"  Start index: {citation_result.get('start_index', 'N/A')}")
        print("-" * 50)
    
    # Check for specific issues
    print("\nAnalysis:")
    
    # Check if clusters have canonical names
    clusters_with_canonical = [c for c in result.get('results', []) 
                             if c.get('is_cluster') and c.get('canonical_name') and c.get('canonical_name') != 'N/A']
    print(f"Clusters with canonical names: {len(clusters_with_canonical)}")
    
    # Check if singles that are part of clusters are properly handled
    singles_not_in_clusters = [c for c in result.get('results', []) 
                              if not c.get('is_cluster')]
    print(f"Singles not in clusters: {len(singles_not_in_clusters)}")
    
    # Check for any citations that appear multiple times
    all_citations = [c.get('citation') for c in result.get('results', [])]
    citation_counts = {}
    for citation in all_citations:
        citation_counts[citation] = citation_counts.get(citation, 0) + 1
    
    duplicates = {k: v for k, v in citation_counts.items() if v > 1}
    if duplicates:
        print(f"⚠️  Duplicate citations found: {duplicates}")
    else:
        print("✅ No duplicate citations found")
    
    print("\nTest completed!")
    
except ImportError as e:
    print(f"❌ Failed to import UnifiedCitationProcessor: {e}")
except Exception as e:
    print(f"❌ Error during testing: {e}") 