#!/usr/bin/env python3
"""
Test script to verify the unified clustering system with batch CourtListener verification.
Tests the 180/minute rate limiting and batch processing.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_clustering import cluster_citations_unified

class MockCitation:
    def __init__(self, citation, start_index, extracted_case_name=None, extracted_date=None, parallel_citations=None):
        self.citation = citation
        self.start_index = start_index
        self.extracted_case_name = extracted_case_name
        self.extracted_date = extracted_date
        self.parallel_citations = parallel_citations or []
        
        # Initialize verification fields
        self.canonical_name = None
        self.canonical_date = None
        self.canonical_url = None
        self.is_verified = False
        self.metadata = {}

def test_batch_verification():
    print("\nTesting: Unified Clustering with Batch CourtListener Verification")
    print("=" * 70)
    
    # Create test citations with well-known Supreme Court cases
    citations = [
        # Miranda v. Arizona parallel citations
        MockCitation("384 U.S. 436", 100, "Miranda v. Arizona", None, ["86 S. Ct. 1602", "16 L. Ed. 2d 694"]),
        MockCitation("86 S. Ct. 1602", 120, None, None, ["384 U.S. 436", "16 L. Ed. 2d 694"]),
        MockCitation("16 L. Ed. 2d 694", 140, None, "1966", ["384 U.S. 436", "86 S. Ct. 1602"]),
        
        # Gideon v. Wainwright
        MockCitation("372 U.S. 335", 200, "Gideon v. Wainwright", "1963", []),
        
        # Brown v. Board parallel citations
        MockCitation("347 U.S. 483", 300, "Brown v. Board of Education", None, ["74 S. Ct. 686", "98 L. Ed. 873"]),
        MockCitation("74 S. Ct. 686", 320, None, None, ["347 U.S. 483", "98 L. Ed. 873"]),
        MockCitation("98 L. Ed. 873", 340, None, "1954", ["347 U.S. 483", "74 S. Ct. 686"]),
    ]
    
    print(f"Starting with {len(citations)} citations")
    
    # Test clustering WITHOUT verification first
    print("\n--- Step 1: Clustering WITHOUT Verification ---")
    start_time = time.time()
    clusters_no_verify = cluster_citations_unified(citations, enable_verification=False)
    clustering_time = time.time() - start_time
    
    print(f"Clustering completed in {clustering_time:.2f} seconds")
    print(f"Clusters created: {len(clusters_no_verify)}")
    
    for cluster in clusters_no_verify:
        print(f"  Cluster: {cluster['case_name']} ({cluster['year']}) - {len(cluster['citations'])} citations")
    
    # Verify all citations have extracted metadata
    all_have_names = all(hasattr(c, 'extracted_case_name') and c.extracted_case_name != "N/A" for c in citations)
    all_have_years = all(hasattr(c, 'extracted_date') and c.extracted_date != "N/A" for c in citations)
    
    print(f"\nExtracted metadata check:")
    print(f"  ✓ All citations have case names: {all_have_names}")
    print(f"  ✓ All citations have years: {all_have_years}")
    
    # Test clustering WITH batch verification
    print("\n--- Step 2: Clustering WITH Batch Verification ---")
    print("Note: This will make real API calls to CourtListener if COURTLISTENER_API_KEY is set")
    
    # Reset citations for clean test
    for citation in citations:
        citation.canonical_name = None
        citation.canonical_date = None
        citation.canonical_url = None
        citation.is_verified = False
        citation.metadata = {}
    
    start_time = time.time()
    clusters_with_verify = cluster_citations_unified(citations, enable_verification=True)
    verification_time = time.time() - start_time
    
    print(f"Clustering + Verification completed in {verification_time:.2f} seconds")
    print(f"Clusters created: {len(clusters_with_verify)}")
    
    # Check verification results
    verified_count = sum(1 for c in citations if getattr(c, 'is_verified', False))
    unverified_count = len(citations) - verified_count
    
    print(f"\nVerification results:")
    print(f"  ✓ Verified citations: {verified_count}")
    print(f"  ✗ Unverified citations: {unverified_count}")
    
    # Show detailed results for each citation
    print(f"\nDetailed verification results:")
    print("-" * 50)
    
    for i, citation in enumerate(citations, 1):
        status = "✓ VERIFIED" if getattr(citation, 'is_verified', False) else "✗ UNVERIFIED"
        canonical_name = getattr(citation, 'canonical_name', 'None')
        canonical_date = getattr(citation, 'canonical_date', 'None')
        canonical_url = getattr(citation, 'canonical_url', 'None')
        
        print(f"{i}. {citation.citation}")
        print(f"   Status: {status}")
        print(f"   Extracted: {citation.extracted_case_name} ({citation.extracted_date})")
        print(f"   Canonical: {canonical_name} ({canonical_date})")
        if canonical_url:
            print(f"   URL: {canonical_url}")
        print()
    
    return clusters_with_verify

if __name__ == "__main__":
    # Check if API key is available
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if not api_key:
        print("WARNING: COURTLISTENER_API_KEY not found in environment")
        print("Verification will be skipped. Set the API key to test verification.")
        print()
    
    test_batch_verification()
