"""
Test script for the unified citation clustering system.

This verifies that the new UnifiedCitationClusterer correctly implements
the user's specified logic:
1. Extract case name from FIRST citation in sequence
2. Extract year from LAST citation in sequence  
3. Propagate both to all citations in cluster
4. Cluster by same extracted name AND year
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_clustering import UnifiedCitationClusterer, cluster_citations_unified
from src.models import CitationResult

def create_test_citation(citation_text, start_index, case_name=None, date=None):
    """Helper to create test citation objects."""
    citation = CitationResult(
        citation=citation_text,
        start_index=start_index,
        end_index=start_index + len(citation_text),
        extracted_case_name=case_name,
        extracted_date=date,
        parallel_citations=[],
        metadata={}
    )
    return citation

def test_basic_clustering():
    """Test basic clustering with case name from first, year from last."""
    print("\n=== Test 1: Basic Clustering (First Name, Last Year) ===")
    
    # Create test citations that should cluster together
    citations = [
        create_test_citation("123 F.3d 456", 0, "Smith v. Jones", None),
        create_test_citation("789 S. Ct. 101", 50, None, "2020"),
        create_test_citation("234 L. Ed. 2d 567", 100, None, "2020"),
    ]
    
    # Mark them as parallel citations
    citations[0].parallel_citations = ["789 S. Ct. 101", "234 L. Ed. 2d 567"]
    citations[1].parallel_citations = ["123 F.3d 456", "234 L. Ed. 2d 567"]
    citations[2].parallel_citations = ["123 F.3d 456", "789 S. Ct. 101"]
    
    clusterer = UnifiedCitationClusterer(config={'debug_mode': True})
    clusters = clusterer.cluster_citations(citations)
    
    print(f"Created {len(clusters)} clusters")
    
    if clusters:
        cluster = clusters[0]
        print(f"Cluster case name: {cluster['case_name']}")
        print(f"Cluster year: {cluster['year']}")
        print(f"Citations in cluster: {cluster['citations']}")
        
        # Verify propagation worked
        for citation in citations:
            print(f"Citation {citation.citation}: name='{citation.extracted_case_name}', date='{citation.extracted_date}'")
        
        # Expected: All citations should have "Smith v. Jones" and "2020"
        expected_name = "Smith v. Jones"
        expected_year = "2020"
        
        success = True
        for citation in citations:
            if citation.extracted_case_name != expected_name:
                print(f"ERROR: Expected name '{expected_name}', got '{citation.extracted_case_name}'")
                success = False
            if citation.extracted_date != expected_year:
                print(f"ERROR: Expected year '{expected_year}', got '{citation.extracted_date}'")
                success = False
        
        if success:
            print("✓ Test 1 PASSED: Case name from first, year from last, propagated correctly")
        else:
            print("✗ Test 1 FAILED")
    else:
        print("✗ Test 1 FAILED: No clusters created")

def test_multiple_clusters():
    """Test clustering with multiple distinct clusters."""
    print("\n=== Test 2: Multiple Distinct Clusters ===")
    
    citations = [
        # First cluster: Brown v. Board
        create_test_citation("347 U.S. 483", 0, "Brown v. Board", None),
        create_test_citation("98 L. Ed. 873", 50, None, "1954"),
        
        # Second cluster: Miranda v. Arizona  
        create_test_citation("384 U.S. 436", 200, "Miranda v. Arizona", None),
        create_test_citation("86 S. Ct. 1602", 250, None, "1966"),
        create_test_citation("16 L. Ed. 2d 694", 300, None, "1966"),
    ]
    
    # Set up parallel relationships
    citations[0].parallel_citations = ["98 L. Ed. 873"]
    citations[1].parallel_citations = ["347 U.S. 483"]
    
    citations[2].parallel_citations = ["86 S. Ct. 1602", "16 L. Ed. 2d 694"]
    citations[3].parallel_citations = ["384 U.S. 436", "16 L. Ed. 2d 694"]
    citations[4].parallel_citations = ["384 U.S. 436", "86 S. Ct. 1602"]
    
    clusterer = UnifiedCitationClusterer()
    clusters = clusterer.cluster_citations(citations)
    
    print(f"Created {len(clusters)} clusters")
    
    expected_clusters = 2
    if len(clusters) == expected_clusters:
        print("✓ Test 2 PASSED: Correct number of clusters created")
        
        for i, cluster in enumerate(clusters):
            print(f"Cluster {i+1}: {cluster['case_name']} ({cluster['year']}) - {cluster['size']} citations")
    else:
        print(f"✗ Test 2 FAILED: Expected {expected_clusters} clusters, got {len(clusters)}")

def test_no_clustering_when_different_cases():
    """Test that different cases don't get clustered together."""
    print("\n=== Test 3: No Clustering for Different Cases ===")
    
    citations = [
        create_test_citation("123 F.3d 456", 0, "Smith v. Jones", "2020"),
        create_test_citation("789 F.3d 101", 100, "Brown v. Davis", "2021"),
    ]
    
    clusterer = UnifiedCitationClusterer()
    clusters = clusterer.cluster_citations(citations)
    
    print(f"Created {len(clusters)} clusters")
    
    if len(clusters) == 0:
        print("✓ Test 3 PASSED: No clusters created for different cases")
    else:
        print("✗ Test 3 FAILED: Clusters created for different cases")

def test_single_citation_clusters():
    """Test that single citations are also put into clusters (frontend requirement)."""
    print("\n=== Test 4: Single Citation Clusters ===")
    
    citations = [
        create_test_citation("123 F.3d 456", 0, "Single v. Case", "2023"),
    ]
    
    clusterer = UnifiedCitationClusterer()
    clusters = clusterer.cluster_citations(citations)
    
    print(f"Created {len(clusters)} clusters for single citation")
    
    if len(clusters) == 1:
        cluster = clusters[0]
        print(f"Single cluster: {cluster['case_name']} ({cluster['year']}) - {cluster['size']} citation")
        print("✓ Test 4 PASSED: Single citations are properly clustered")
    else:
        print("✗ Test 4 FAILED: Single citation not clustered")

def test_convenience_function():
    """Test the convenience function cluster_citations_unified."""
    print("\n=== Test 5: Convenience Function ===")
    
    citations = [
        create_test_citation("123 F.3d 456", 0, "Test v. Case", None),
        create_test_citation("789 S. Ct. 101", 50, None, "2022"),
    ]
    
    citations[0].parallel_citations = ["789 S. Ct. 101"]
    citations[1].parallel_citations = ["123 F.3d 456"]
    
    clusters = cluster_citations_unified(citations)
    
    print(f"Created {len(clusters)} clusters using convenience function")
    
    if len(clusters) == 1:
        print("✓ Test 5 PASSED: Convenience function works correctly")
    else:
        print("✗ Test 5 FAILED: Convenience function didn't work")

def main():
    """Run all tests for the unified clustering system."""
    print("Testing Unified Citation Clustering System")
    print("=" * 50)
    
    try:
        test_basic_clustering()
        test_multiple_clusters()
        test_no_clustering_when_different_cases()
        test_single_citation_clusters()
        test_convenience_function()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
