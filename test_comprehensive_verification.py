#!/usr/bin/env python3
"""
Test script to verify the complete unified clustering and verification system.
Tests both CourtListener API and fallback verification sources.
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

def test_comprehensive_verification():
    print("\nTesting: Complete Unified Clustering + Verification System")
    print("=" * 70)
    print("This test includes CourtListener API + Fallback verification")
    print()
    
    # Create test citations with mix of well-known and potentially obscure cases
    citations = [
        # Well-known Supreme Court cases (likely in CourtListener)
        MockCitation("384 U.S. 436", 100, "Miranda v. Arizona", None, ["86 S. Ct. 1602", "16 L. Ed. 2d 694"]),
        MockCitation("86 S. Ct. 1602", 120, None, None, ["384 U.S. 436", "16 L. Ed. 2d 694"]),
        MockCitation("16 L. Ed. 2d 694", 140, None, "1966", ["384 U.S. 436", "86 S. Ct. 1602"]),
        
        # Another well-known case
        MockCitation("347 U.S. 483", 200, "Brown v. Board of Education", "1954", []),
        
        # Potentially less common citations (may need fallback)
        MockCitation("123 Wash. 2d 456", 300, "State v. Example", "2010", []),
        MockCitation("789 P.2d 123", 350, "Example Corp. v. Test Inc.", "1995", []),
        
        # Law review citation (likely needs fallback)
        MockCitation("85 Harv. L. Rev. 1032", 400, "Legal Analysis Article", "1972", []),
    ]
    
    print(f"Starting with {len(citations)} citations")
    print("Mix includes:")
    print("  - Well-known Supreme Court cases (likely in CourtListener)")
    print("  - State court cases (may need fallback)")
    print("  - Law review citations (likely need fallback)")
    print()
    
    # Test the complete verification pipeline
    print("--- Running Complete Verification Pipeline ---")
    print("1. Clustering citations")
    print("2. Extracting metadata (name from first, year from last)")
    print("3. Batch verification with CourtListener API")
    print("4. Fallback verification for unverified citations")
    print()
    
    start_time = time.time()
    clusters = cluster_citations_unified(citations, enable_verification=True)
    total_time = time.time() - start_time
    
    print(f"Complete pipeline completed in {total_time:.2f} seconds")
    print(f"Clusters created: {len(clusters)}")
    print()
    
    # Analyze verification results
    courtlistener_verified = 0
    fallback_verified = 0
    unverified = 0
    
    verification_sources = {}
    
    for citation in citations:
        if getattr(citation, 'is_verified', False):
            metadata = getattr(citation, 'metadata', {})
            source = metadata.get('verification_source', 'unknown')
            
            if 'courtlistener' in source:
                courtlistener_verified += 1
            elif 'fallback' in source:
                fallback_verified += 1
            
            verification_sources[source] = verification_sources.get(source, 0) + 1
        else:
            unverified += 1
    
    print("Verification Results Summary:")
    print("-" * 40)
    print(f"  ✓ CourtListener verified: {courtlistener_verified}")
    print(f"  ✓ Fallback verified: {fallback_verified}")
    print(f"  ✗ Unverified: {unverified}")
    print(f"  📊 Total verification rate: {((courtlistener_verified + fallback_verified) / len(citations) * 100):.1f}%")
    print()
    
    if verification_sources:
        print("Verification Sources Used:")
        for source, count in verification_sources.items():
            print(f"  - {source}: {count} citations")
        print()
    
    # Show detailed results for each citation
    print("Detailed Verification Results:")
    print("-" * 50)
    
    for i, citation in enumerate(citations, 1):
        status = "✓ VERIFIED" if getattr(citation, 'is_verified', False) else "✗ UNVERIFIED"
        canonical_name = getattr(citation, 'canonical_name', 'None')
        canonical_date = getattr(citation, 'canonical_date', 'None')
        canonical_url = getattr(citation, 'canonical_url', 'None')
        
        metadata = getattr(citation, 'metadata', {})
        source = metadata.get('verification_source', 'none')
        confidence = metadata.get('fallback_confidence', metadata.get('confidence', 'N/A'))
        
        print(f"{i}. {citation.citation}")
        print(f"   Status: {status}")
        print(f"   Source: {source}")
        if confidence != 'N/A':
            print(f"   Confidence: {confidence}")
        print(f"   Extracted: {citation.extracted_case_name} ({citation.extracted_date})")
        print(f"   Canonical: {canonical_name} ({canonical_date})")
        if canonical_url and canonical_url != 'None':
            print(f"   URL: {canonical_url}")
        print()
    
    # Show cluster information
    print("Cluster Information:")
    print("-" * 30)
    for cluster in clusters:
        verified_count = sum(1 for c in cluster['citation_objects'] if getattr(c, 'is_verified', False))
        print(f"  Cluster: {cluster['case_name']} ({cluster['year']})")
        print(f"    Citations: {cluster['size']} ({verified_count} verified)")
        print()
    
    return clusters

def test_api_key_status():
    """Check if API keys are available for testing"""
    print("API Key Status:")
    print("-" * 20)
    
    courtlistener_key = os.getenv('COURTLISTENER_API_KEY')
    if courtlistener_key:
        print("  ✓ COURTLISTENER_API_KEY: Available")
    else:
        print("  ✗ COURTLISTENER_API_KEY: Not found")
        print("    Set this to test CourtListener verification")
    
    print()

if __name__ == "__main__":
    test_api_key_status()
    test_comprehensive_verification()
