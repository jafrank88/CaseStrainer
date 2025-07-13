#!/usr/bin/env python3
"""
Test script for improved citation clustering
============================================

This script demonstrates the improved clustering system and compares it
with the old clustering approach.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from improved_citation_clustering import CitationData, ImprovedCitationClusterer, apply_improved_clustering
import json

def create_test_citations():
    """Create test citation data for demonstration"""
    
    # Test case 1: Valid parallel citations (should be clustered)
    valid_parallels = [
        CitationData(
            citation="200 Wn.2d 72",
            extracted_case_name="Convoyant, LLC v. DeepThink, LLC",
            extracted_date="2022",
            confidence=0.9,
            start_index=100,
            end_index=115,
            context="Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)",
            verified=True
        ),
        CitationData(
            citation="514 P.3d 643",
            extracted_case_name="Convoyant, LLC v. DeepThink, LLC",
            extracted_date="2022",
            confidence=0.9,
            start_index=117,
            end_index=130,
            context="Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)",
            verified=True
        )
    ]
    
    # Test case 2: Different cases (should NOT be clustered)
    different_cases = [
        CitationData(
            citation="171 Wn.2d 486",
            extracted_case_name="Carlson v. Global Client Solutions, LLC",
            extracted_date="2011",
            confidence=0.8,
            start_index=200,
            end_index=215,
            context="Carlson v. Global Client Solutions, LLC, 171 Wn.2d 486, 256 P.3d 321 (2011)",
            verified=True
        ),
        CitationData(
            citation="146 Wn.2d 1",
            extracted_case_name="Department of Ecology v. Campbell & Gwinn, LLC",
            extracted_date="2003",
            confidence=0.8,
            start_index=300,
            end_index=315,
            context="Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 43 P.3d 4 (2003)",
            verified=True
        )
    ]
    
    # Test case 3: Temporally inconsistent (should NOT be clustered)
    temporal_inconsistent = [
        CitationData(
            citation="200 Wn.2d 72",
            extracted_case_name="Smith v. Jones",
            extracted_date="2022",
            confidence=0.7,
            start_index=400,
            end_index=415,
            context="Smith v. Jones, 200 Wn.2d 72 (2022)",
            verified=False
        ),
        CitationData(
            citation="150 Wn.2d 100",
            extracted_case_name="Smith v. Jones",
            extracted_date="2010",
            confidence=0.7,
            start_index=450,
            end_index=465,
            context="Smith v. Jones, 150 Wn.2d 100 (2010)",
            verified=False
        )
    ]
    
    # Test case 4: Low confidence citations (should be filtered out)
    low_confidence = [
        CitationData(
            citation="123 F.3d 456",
            extracted_case_name="Unknown Case",
            extracted_date="2020",
            confidence=0.3,  # Below threshold
            start_index=500,
            end_index=515,
            context="Some case, 123 F.3d 456 (2020)",
            verified=False
        ),
        CitationData(
            citation="456 F.Supp. 789",
            extracted_case_name="Unknown Case",
            extracted_date="2020",
            confidence=0.4,  # Below threshold
            start_index=550,
            end_index=565,
            context="Some case, 456 F.Supp. 789 (2020)",
            verified=False
        )
    ]
    
    # Test case 5: Court incompatible (should NOT be clustered)
    court_incompatible = [
        CitationData(
            citation="200 Wn.2d 72",
            extracted_case_name="State Case",
            extracted_date="2022",
            confidence=0.8,
            start_index=600,
            end_index=615,
            context="State Case, 200 Wn.2d 72 (2022)",
            verified=True
        ),
        CitationData(
            citation="123 F.3d 456",
            extracted_case_name="Federal Case",
            extracted_date="2022",
            confidence=0.8,
            start_index=650,
            end_index=665,
            context="Federal Case, 123 F.3d 456 (2022)",
            verified=True
        )
    ]
    
    return {
        'valid_parallels': valid_parallels,
        'different_cases': different_cases,
        'temporal_inconsistent': temporal_inconsistent,
        'low_confidence': low_confidence,
        'court_incompatible': court_incompatible
    }

def test_improved_clustering():
    """Test the improved clustering system"""
    
    print("=== Testing Improved Citation Clustering ===\n")
    
    # Create test data
    test_cases = create_test_citations()
    
    # Initialize clusterer with debug mode
    clusterer = ImprovedCitationClusterer({
        'similarity_threshold': 0.85,
        'min_confidence': 0.6,
        'max_cluster_distance': 1000,
        'enable_validation': True,
        'debug_mode': True,
        'prevent_false_clusters': True,
        'case_name_similarity_threshold': 0.8,
        'temporal_tolerance_years': 2
    })
    
    # Test each case
    for case_name, citations in test_cases.items():
        print(f"Test Case: {case_name.replace('_', ' ').title()}")
        print(f"Input citations: {len(citations)}")
        
        # Perform clustering
        clusters = clusterer.cluster_parallel_citations(citations)
        
        print(f"Output clusters: {len(clusters)}")
        
        for cluster_id, cluster_citations in clusters.items():
            print(f"  Cluster {cluster_id}: {len(cluster_citations)} citations")
            for citation in cluster_citations:
                print(f"    - {citation.citation} ({citation.extracted_case_name})")
        
        # Calculate metrics
        metrics = clusterer.calculate_clustering_metrics(citations, clusters)
        print(f"Metrics: {metrics}")
        print()

def compare_with_old_system():
    """Compare improved clustering with old system behavior"""
    
    print("=== Comparison with Old System ===\n")
    
    # Sample text that would cause over-clustering in old system
    sample_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution 
    of that question is necessary to resolve a case before the federal court. RCW 2.60.020; 
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions 
    are questions of law we review de novo. Carlson v. Global Client Solutions, LLC, 171 Wn.2d 486, 
    493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Department of Ecology 
    v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    # Create citations from this text
    citations = [
        CitationData(
            citation="200 Wn.2d 72",
            extracted_case_name="Convoyant, LLC v. DeepThink, LLC",
            extracted_date="2022",
            confidence=0.9,
            start_index=200,
            end_index=215,
            context=sample_text,
            verified=True
        ),
        CitationData(
            citation="514 P.3d 643",
            extracted_case_name="Convoyant, LLC v. DeepThink, LLC",
            extracted_date="2022",
            confidence=0.9,
            start_index=217,
            end_index=230,
            context=sample_text,
            verified=True
        ),
        CitationData(
            citation="171 Wn.2d 486",
            extracted_case_name="Carlson v. Global Client Solutions, LLC",
            extracted_date="2011",
            confidence=0.8,
            start_index=350,
            end_index=365,
            context=sample_text,
            verified=True
        ),
        CitationData(
            citation="256 P.3d 321",
            extracted_case_name="Carlson v. Global Client Solutions, LLC",
            extracted_date="2011",
            confidence=0.8,
            start_index=367,
            end_index=380,
            context=sample_text,
            verified=True
        ),
        CitationData(
            citation="146 Wn.2d 1",
            extracted_case_name="Department of Ecology v. Campbell & Gwinn, LLC",
            extracted_date="2003",
            confidence=0.8,
            start_index=500,
            end_index=515,
            context=sample_text,
            verified=True
        ),
        CitationData(
            citation="43 P.3d 4",
            extracted_case_name="Department of Ecology v. Campbell & Gwinn, LLC",
            extracted_date="2003",
            confidence=0.8,
            start_index=517,
            end_index=530,
            context=sample_text,
            verified=True
        )
    ]
    
    print("Sample text citations:")
    for i, citation in enumerate(citations):
        print(f"  {i+1}. {citation.citation} - {citation.extracted_case_name} ({citation.extracted_date})")
    
    print("\nOld system behavior (estimated):")
    print("  - Would create 3 clusters (one per case)")
    print("  - Each cluster would contain 2 parallel citations")
    print("  - Total clusters: 3")
    print("  - Clustering ratio: 50% (3/6)")
    
    print("\nImproved system behavior:")
    clusters, metrics = apply_improved_clustering(citations, {
        'similarity_threshold': 0.85,
        'min_confidence': 0.6,
        'enable_validation': True,
        'debug_mode': True
    })
    
    print(f"  - Created {metrics['cluster_count']} clusters")
    print(f"  - Clustering ratio: {metrics['clustering_ratio']:.1%}")
    print(f"  - False clusters prevented: {metrics['false_clusters_prevented']}")
    print(f"  - Average confidence: {metrics['avg_confidence']:.1%}")
    
    print("\nDetailed clusters:")
    for cluster_id, cluster_citations in clusters.items():
        print(f"  {cluster_id}:")
        for citation in cluster_citations:
            print(f"    - {citation.citation} ({citation.extracted_case_name})")

def demonstrate_integration():
    """Demonstrate how to integrate the improved clustering"""
    
    print("\n=== Integration Example ===\n")
    
    # Example of how to integrate with existing code
    print("Integration with existing UnifiedCitationProcessorV2:")
    print()
    
    integration_code = '''
# In UnifiedCitationProcessorV2.process_text() method:

# Replace the old clustering logic:
# citations = self._detect_parallel_citations(citations, text)

# With improved clustering:
from improved_citation_clustering import apply_improved_clustering

# Convert citations to the format expected by improved clustering
citation_data = convert_citation_results_to_data(citations)

# Apply improved clustering
clusters, metrics = apply_improved_clustering(citations, {
    'similarity_threshold': 0.85,
    'min_confidence': 0.6,
    'enable_validation': True,
    'debug_mode': self.config.debug_mode
})

# Update citation metadata with cluster information
for cluster_id, cluster_citations in clusters.items():
    for citation in cluster_citations:
        # Find corresponding citation in original list
        for orig_citation in citations:
            if orig_citation.citation == citation.citation:
                orig_citation.metadata.update({
                    'is_in_cluster': True,
                    'cluster_id': cluster_id,
                    'cluster_size': len(cluster_citations),
                    'cluster_members': [c.citation for c in cluster_citations],
                    'improved_clustering': True
                })
                break

# Log metrics
logger.info(f"Improved clustering metrics: {metrics}")
'''
    
    print(integration_code)

def main():
    """Run all tests and demonstrations"""
    
    print("IMPROVED CITATION CLUSTERING SYSTEM")
    print("=" * 50)
    
    # Test individual cases
    test_improved_clustering()
    
    # Compare with old system
    compare_with_old_system()
    
    # Show integration example
    demonstrate_integration()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("The improved clustering system provides:")
    print("• Better validation of parallel citations")
    print("• Prevention of false clusters")
    print("• Confidence-based filtering")
    print("• Temporal consistency checks")
    print("• Court compatibility validation")
    print("• More accurate clustering metrics")
    print()
    print("Next steps:")
    print("1. Integrate into UnifiedCitationProcessorV2")
    print("2. Test with real document data")
    print("3. Monitor clustering quality metrics")
    print("4. Gradually replace old clustering logic")

if __name__ == "__main__":
    main() 