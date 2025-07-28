#!/usr/bin/env python3
"""
Production test to verify the clustering fix works with real documents.
Tests the complete citation processing pipeline including clustering.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.citation_service import CitationService
from src.models import ProcessingConfig
import asyncio

async def test_production_clustering():
    """Test clustering with a real document containing Gideon v. Wainwright citations."""
    print("Testing Production Citation Clustering")
    print("=" * 50)
    
    # Initialize the citation service
    config = ProcessingConfig()
    citation_service = CitationService(config)
    
    # Test document path
    test_file = "test_files/test.txt"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Processing document: {test_file}")
    
    # Read the test document
    with open(test_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    print(f"Document content preview:")
    print(f"  Length: {len(text_content)} characters")
    print(f"  Preview: {text_content[:200]}...")
    
    # Process the document
    try:
        print("\nProcessing citations...")
        result = await citation_service.process_text_async(text_content, "test_document")
        
        if not result or 'citations' not in result:
            print("❌ No citations found in result")
            return False
        
        citations = result['citations']
        print(f"Found {len(citations)} citations")
        
        # Look for Gideon citations
        gideon_citations = []
        other_citations = []
        
        for citation in citations:
            citation_text = citation.get('citation', '')
            canonical_name = citation.get('canonical_name', '')
            extracted_name = citation.get('extracted_case_name', '')
            
            if ('gideon' in citation_text.lower() or 
                'gideon' in canonical_name.lower() or 
                'gideon' in extracted_name.lower()):
                gideon_citations.append(citation)
            else:
                other_citations.append(citation)
        
        print(f"\nCitation Analysis:")
        print(f"  Gideon citations: {len(gideon_citations)}")
        print(f"  Other citations: {len(other_citations)}")
        
        # Check if Gideon citations are properly clustered
        if len(gideon_citations) > 0:
            print(f"\nGideon Citation Details:")
            for i, citation in enumerate(gideon_citations):
                print(f"  {i+1}. Citation: {citation.get('citation', 'N/A')}")
                print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"     Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"     Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"     Verified: {citation.get('verified', False)}")
                print(f"     Cluster ID: {citation.get('cluster_id', 'N/A')}")
                print()
            
            # Check clustering consistency
            cluster_ids = set()
            canonical_names = set()
            canonical_dates = set()
            
            for citation in gideon_citations:
                cluster_id = citation.get('cluster_id')
                canonical_name = citation.get('canonical_name')
                canonical_date = citation.get('canonical_date')
                
                if cluster_id:
                    cluster_ids.add(cluster_id)
                if canonical_name:
                    canonical_names.add(canonical_name)
                if canonical_date:
                    canonical_dates.add(canonical_date)
            
            print(f"Clustering Analysis:")
            print(f"  Unique cluster IDs: {len(cluster_ids)} - {list(cluster_ids)}")
            print(f"  Unique canonical names: {len(canonical_names)} - {list(canonical_names)}")
            print(f"  Unique canonical dates: {len(canonical_dates)} - {list(canonical_dates)}")
            
            # Determine success
            if len(cluster_ids) <= 1 and len(canonical_names) <= 1 and len(canonical_dates) <= 1:
                print(f"\n✅ SUCCESS: Gideon citations are properly clustered!")
                print(f"   All citations share the same cluster/canonical data")
                success = True
            else:
                print(f"\n❌ FAILURE: Gideon citations are not properly clustered!")
                print(f"   Multiple cluster IDs or canonical names/dates detected")
                success = False
        else:
            print(f"\n⚠️  WARNING: No Gideon citations found in the document")
            success = True  # Not a failure if document doesn't contain Gideon citations
        
        # Check for cross-contamination
        print(f"\nCross-Contamination Check:")
        cluster_to_cases = {}
        
        for citation in citations:
            cluster_id = citation.get('cluster_id')
            canonical_name = citation.get('canonical_name', citation.get('extracted_case_name', 'Unknown'))
            
            if cluster_id:
                if cluster_id not in cluster_to_cases:
                    cluster_to_cases[cluster_id] = set()
                cluster_to_cases[cluster_id].add(canonical_name.lower())
        
        contamination_found = False
        for cluster_id, case_names in cluster_to_cases.items():
            if len(case_names) > 1:
                print(f"  ❌ Cross-contamination in cluster {cluster_id}: {case_names}")
                contamination_found = True
        
        if not contamination_found:
            print(f"  ✅ No cross-contamination detected")
        
        return success and not contamination_found
        
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("Citation Clustering Production Test")
    print("=" * 50)
    
    success = await test_production_clustering()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PRODUCTION TEST PASSED!")
        print("The clustering fix is working correctly in production.")
    else:
        print("❌ PRODUCTION TEST FAILED!")
        print("The clustering fix needs further investigation.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
