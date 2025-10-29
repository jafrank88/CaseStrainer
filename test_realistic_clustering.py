#!/usr/bin/env python3
"""
Test realistic parallel citation clustering as it appears in legal documents
"""

import sys
import os
import json
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_realistic_clustering():
    """Test parallel citations in realistic legal writing format"""
    
    # Test text with parallel citations in realistic format
    test_text = """
    The Colorado Supreme Court's decision in City of Aspen v. Burlingame Ranch II Condo. Owners Ass'n, 2024 CO 46, 551 P.3d 655, 
    represents a significant precedent in condominium law. Similarly, in Martinez v. Rodriguez, 2023 COA 108, 543 P.3d 1059, 
    the court addressed similar issues regarding homeowner association responsibilities.
    """
    
    print("TESTING REALISTIC PARALLEL CLUSTERING")
    print("=" * 60)
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Process the text
    result = await processor.process_text(test_text)
    
    print(f"\nFound {len(result.get('citations', []))} citations")
    print(f"Created {len(result.get('clusters', []))} clusters")
    
    # Check citations
    citations = result.get('citations', [])
    print("\nCITATIONS:")
    for i, cit in enumerate(citations):
        # Convert to dict if it's a CitationResult object
        if hasattr(cit, 'to_dict'):
            cit_dict = cit.to_dict()
        else:
            cit_dict = cit
        
        print(f"{i+1}. {cit_dict.get('citation', 'Unknown')}")
        print(f"   - extracted_case_name: {cit_dict.get('extracted_case_name', 'None')}")
        print(f"   - extracted_date: {cit_dict.get('extracted_date', 'None')}")
        print(f"   - cluster_id: {cit_dict.get('cluster_id', 'None')}")
        print(f"   - is_cluster: {cit_dict.get('is_cluster', False)}")
        print(f"   - cluster_members: {cit_dict.get('cluster_members', [])}")
        print()
    
    # Check clusters
    clusters = result.get('clusters', [])
    print("\nCLUSTERS:")
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i+1}:")
        print(f"   - cluster_id: {cluster.get('cluster_id', 'None')}")
        print(f"   - cluster_case_name: {cluster.get('cluster_case_name', 'None')}")
        print(f"   - cluster_year: {cluster.get('cluster_year', 'None')}")
        print(f"   - citations: {len(cluster.get('citations', []))}")
        for cit in cluster.get('citations', []):
            print(f"     * {cit.get('citation', 'Unknown')}")
        print()
    
    # Verify expectations
    print("VERIFICATION:")
    print("-" * 40)
    
    # Check if 2024 CO 46 and 551 P.3d 655 are clustered
    aspen_co = None
    aspen_p3d = None
    martinez_co = None
    martinez_p3d = None
    
    for cit in citations:
        if hasattr(cit, 'to_dict'):
            cit_dict = cit.to_dict()
        else:
            cit_dict = cit
            
        if '2024 CO 46' in cit_dict.get('citation', ''):
            aspen_co = cit_dict
        elif '551 P.3d 655' in cit_dict.get('citation', ''):
            aspen_p3d = cit_dict
        elif '2023 COA 108' in cit_dict.get('citation', ''):
            martinez_co = cit_dict
        elif '543 P.3d 1059' in cit_dict.get('citation', ''):
            martinez_p3d = cit_dict
    
    # Check Aspen clustering
    if aspen_co and aspen_p3d:
        if aspen_co.get('cluster_id') == aspen_p3d.get('cluster_id'):
            print("✅ PASS: 2024 CO 46 and 551 P.3d 655 are in the same cluster")
            
            # Check if they have the same case name
            if aspen_co.get('extracted_case_name') and aspen_p3d.get('extracted_case_name'):
                if aspen_co.get('extracted_case_name') == aspen_p3d.get('extracted_case_name'):
                    print(f"✅ PASS: Both have same case name: {aspen_co.get('extracted_case_name')[:50]}...")
                else:
                    print("❌ FAIL: Case names don't match")
            else:
                print("⚠️  WARNING: Missing case names")
        else:
            print("❌ FAIL: 2024 CO 46 and 551 P.3d 655 are NOT in the same cluster")
    else:
        print("❌ FAIL: Could not find both Aspen citations")
    
    # Check Martinez clustering
    if martinez_co and martinez_p3d:
        if martinez_co.get('cluster_id') == martinez_p3d.get('cluster_id'):
            print("✅ PASS: 2023 COA 108 and 543 P.3d 1059 are in the same cluster")
        else:
            print("❌ FAIL: 2023 COA 108 and 543 P.3d 1059 are NOT in the same cluster")
    else:
        print("❌ FAIL: Could not find both Martinez citations")
    
    # Check that true_by_parallel is not in the response
    for cit in citations:
        if hasattr(cit, 'to_dict'):
            cit_dict = cit.to_dict()
        else:
            cit_dict = cit
            
        if 'true_by_parallel' in cit_dict:
            print("❌ FAIL: true_by_parallel field still present in citations")
            break
    else:
        print("✅ PASS: true_by_parallel field removed from citations")

if __name__ == "__main__":
    asyncio.run(test_realistic_clustering())
