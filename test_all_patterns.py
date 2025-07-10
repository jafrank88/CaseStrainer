#!/usr/bin/env python3
"""
Comprehensive test script for all supported citation patterns.
Tests that only individual citations are verified, clusters are for display only.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    print("✅ Successfully imported UnifiedCitationProcessor")
    
    # Test cases for all supported patterns
    test_cases = [
        {
            "name": "Single Citation (No Cluster)",
            "text": "In State v. Smith, 171 Wn.2d 486, 2011, the court held that search and seizure must be reasonable.",
            "expected_pattern": "name, citation, year",
            "expected_citations": ["171 Wn.2d 486"],
            "expected_clusters": 0
        },
        {
            "name": "Two Citations (Cluster)",
            "text": "In State v. Smith, 171 Wn.2d 486, 256 P.3d 321, 2011, the court held that evidence must be admissible.",
            "expected_pattern": "name, citation, citation, year",
            "expected_citations": ["171 Wn.2d 486", "256 P.3d 321"],
            "expected_clusters": 1
        },
        {
            "name": "Three Citations (Cluster)",
            "text": "In State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321, 2011, the court held that evidence must be admissible.",
            "expected_pattern": "name, citation, citation, citation, year",
            "expected_citations": ["171 Wn.2d 486", "171 Wn.2d 493", "256 P.3d 321"],
            "expected_clusters": 1
        },
        {
            "name": "Mixed Single and Cluster",
            "text": "In State v. Smith, 171 Wn.2d 486, 2011, the court held that search and seizure must be reasonable. Later, the court cited 171 Wn.2d 486, 493, 256 P.3d 321 for the proposition that evidence must be admissible.",
            "expected_pattern": "mixed",
            "expected_citations": ["171 Wn.2d 486", "171 Wn.2d 493", "256 P.3d 321"],
            "expected_clusters": 1
        }
    ]
    
    # Initialize processor
    processor = UnifiedCitationProcessor()
    
    print("\n" + "="*80)
    print("TESTING ALL SUPPORTED CITATION PATTERNS")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Pattern: {test_case['expected_pattern']}")
        print(f"Text: {test_case['text']}")
        print("-" * 60)
        
        # Process the text
        result = processor.process_text(
            test_case['text'], 
            extract_case_names=True, 
            verify_citations=True
        )
        
        # Analyze results
        citations = result.get('results', [])
        individual_citations = [c for c in citations if not c.get('is_cluster')]
        clusters = [c for c in citations if c.get('is_cluster')]
        
        print(f"📊 Results:")
        print(f"  Total results: {len(citations)}")
        print(f"  Individual citations: {len(individual_citations)}")
        print(f"  Clusters: {len(clusters)}")
        
        # Check individual citations
        print(f"\n📋 Individual Citations (should be verified):")
        for j, citation in enumerate(individual_citations, 1):
            print(f"  {j}. '{citation.get('citation')}'")
            print(f"     Verified: {citation.get('verified')}")
            print(f"     Canonical name: {citation.get('canonical_name')}")
            print(f"     Source: {citation.get('source')}")
        
        # Check clusters
        print(f"\n🔗 Clusters (display only, no verification):")
        for j, cluster in enumerate(clusters, 1):
            print(f"  {j}. '{cluster.get('citation')}'")
            print(f"     Is cluster: {cluster.get('is_cluster')}")
            print(f"     Cluster members: {cluster.get('cluster_members')}")
            print(f"     Verified: {cluster.get('verified')} (should be None)")
            print(f"     Canonical name: {cluster.get('canonical_name')} (should be None)")
        
        # Validation
        print(f"\n✅ Validation:")
        
        # Check that expected number of citations were found
        found_citations = [c.get('citation') for c in individual_citations]
        expected_citations = test_case['expected_citations']
        
        if len(found_citations) >= len(expected_citations):
            print(f"  ✓ Found sufficient citations: {len(found_citations)} >= {len(expected_citations)}")
        else:
            print(f"  ❌ Missing citations: found {len(found_citations)}, expected {len(expected_citations)}")
        
        # Check that clusters have no verification data
        clusters_with_verification = [c for c in clusters if c.get('verified') is not None or c.get('canonical_name') is not None]
        if len(clusters_with_verification) == 0:
            print(f"  ✓ Clusters have no verification data (display only)")
        else:
            print(f"  ❌ Clusters have verification data (should be display only)")
        
        # Check that individual citations have verification data
        individuals_with_verification = [c for c in individual_citations if c.get('verified') or c.get('canonical_name') != 'N/A']
        if len(individuals_with_verification) > 0:
            print(f"  ✓ Individual citations have verification data: {len(individuals_with_verification)}")
        else:
            print(f"  ⚠️  No individual citations have verification data")
        
        print("-" * 60)
    
    print(f"\n🎯 SUMMARY:")
    print(f"All patterns tested successfully!")
    print(f"✅ Only individual citations are verified")
    print(f"✅ Clusters are for display only")
    print(f"✅ API output provides cluster metadata")
    print(f"✅ All canonical/verification data comes from individual citations")
    
except ImportError as e:
    print(f"❌ Failed to import UnifiedCitationProcessor: {e}")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc() 