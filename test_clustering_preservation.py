#!/usr/bin/env python3
"""
Test if clustering preserves verification source information
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_clustering_master import cluster_citations_unified_master
from src.models import CitationResult

def test_clustering_preservation():
    """Test if clustering preserves verification source information."""
    
    print("=" * 60)
    print("TESTING CLUSTERING SOURCE PRESERVATION")
    print("=" * 60)
    
    # Create pre-verified citations (like from pre-verification)
    citations = [
        CitationResult(
            citation="377 U.S. 33",
            extracted_case_name="Permian Basin Area Rate Cases v. FPC",
            extracted_date="1974",
            start_index=0,
            end_index=10,
            verified=True,
            canonical_name="Federal Power Commission v. Texaco Inc.",
            canonical_date="1964-06-15",
            canonical_url="https://www.courtlistener.com/opinion/106806/",
            source="courtlistener_lookup_batch"  # This should be preserved
        ),
        CitationResult(
            citation="382 U.S. 154", 
            extracted_case_name="Permian Basin Area Rate Cases v. FPC",
            extracted_date="1974",
            start_index=20,
            end_index=30,
            verified=True,
            canonical_name="Seaboard Air Line Railroad Co. v. United States",
            canonical_date="1965-12-06",
            canonical_url="https://www.courtlistener.com/opinion/107118/",
            source="courtlistener_lookup_batch"  # This should be preserved
        ),
        CitationResult(
            citation="999 U.S. 999",  # This one is not verified
            extracted_case_name="Fake Case v. Fake Defendant",
            extracted_date="2024",
            start_index=40,
            end_index=50,
            verified=False,
            source="Unknown"
        )
    ]
    
    print(f"Testing {len(citations)} citations...")
    print()
    
    print("BEFORE CLUSTERING:")
    for i, cit in enumerate(citations):
        print(f"Citation {i+1}: {cit.citation}")
        print(f"  verified: {cit.verified}")
        print(f"  source: {cit.source}")
        print()
    
    try:
        # Run clustering with verification enabled
        print("🔥 Running clustering with verification...")
        clusters = cluster_citations_unified_master(
            citations=citations,
            original_text="test text",
            enable_verification=True
        )
        
        print("=" * 60)
        print("AFTER CLUSTERING")
        print("=" * 60)
        print(f"Clusters created: {len(clusters)}")
        print()
        
        # Check what happened to the source information
        sources_preserved = 0
        total_verified = 0
        
        for i, cluster in enumerate(clusters):
            cluster_citations = cluster.get('citations', [])
            print(f"Cluster {i+1}: {len(cluster_citations)} citations")
            
            for cit_dict in cluster_citations:
                if isinstance(cit_dict, dict):
                    citation = cit_dict.get('citation', 'Unknown')
                    verified = cit_dict.get('verified', False)
                    source = cit_dict.get('source', 'Unknown')
                    
                    print(f"  {citation}: verified={verified}, source={source}")
                    
                    if verified:
                        total_verified += 1
                        if source == 'courtlistener_lookup_batch':
                            sources_preserved += 1
        
        print()
        print("PRESERVATION ANALYSIS:")
        print(f"Total verified citations: {total_verified}")
        print(f"Sources preserved correctly: {sources_preserved}")
        
        if sources_preserved == total_verified and total_verified > 0:
            print("✅ SOURCE PRESERVATION WORKING: All verified citations have correct sources")
            return True
        elif total_verified > 0:
            print("⚠️  PARTIAL PRESERVATION: Some sources lost")
            return False
        else:
            print("❌ NO VERIFIED CITATIONS: All verification lost")
            return False
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_clustering_preservation()
    sys.exit(0 if success else 1)
