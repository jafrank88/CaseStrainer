#!/usr/bin/env python3
"""
Test the clustering and date fixes
"""

import sys
import os
import json
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_clustering_fixes():
    """Test that parallel citations are now properly clustered and dates are propagated"""
    
    # Test text with parallel citations that should cluster
    test_text = """
    In the case of City of Aspen v. Burlingame Ranch II Condo. Owners Ass'n, the Colorado 
    Supreme Court considered the issue at 2024 CO 46. The case was also reported at 
    551 P.3d 655. This is an important precedent for Colorado condominium law.
    
    Another example is Colorado Supreme Court case 2023 COA 108, also found at 
    543 P.3d 1059, which addressed similar issues.
    """
    
    print("TESTING CLUSTERING AND DATE FIXES")
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
    
    # Check if 2024 CO 46 and 551 P.3d 655 are in the same cluster
    aspen_co = None
    aspen_p3d = None
    
    for cit in citations:
        # Convert to dict if it's a CitationResult object
        if hasattr(cit, 'to_dict'):
            cit_dict = cit.to_dict()
        else:
            cit_dict = cit
            
        if '2024 CO 46' in cit_dict.get('citation', ''):
            aspen_co = cit_dict
        elif '551 P.3d 655' in cit_dict.get('citation', ''):
            aspen_p3d = cit_dict
    
    if aspen_co and aspen_p3d:
        if aspen_co.get('cluster_id') == aspen_p3d.get('cluster_id'):
            print("✅ PASS: 2024 CO 46 and 551 P.3d 655 are in the same cluster")
            
            # Check date propagation
            if aspen_co.get('extracted_date') or aspen_p3d.get('extracted_date'):
                print("✅ PASS: At least one citation has a date")
                
                # Check if P.3d got date from CO citation
                if aspen_p3d.get('extracted_date'):
                    print(f"✅ PASS: P.3d citation has date: {aspen_p3d.get('extracted_date')}")
                else:
                    print("❌ FAIL: P.3d citation did not get date propagated")
            else:
                print("❌ FAIL: Neither citation has a date")
        else:
            print("❌ FAIL: 2024 CO 46 and 551 P.3d 655 are NOT in the same cluster")
            print(f"   CO cluster_id: {aspen_co.get('cluster_id')}")
            print(f"   P.3d cluster_id: {aspen_p3d.get('cluster_id')}")
    else:
        print("❌ FAIL: Could not find both Aspen citations")
    
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
    
    for cluster in clusters:
        for cit in cluster.get('citations', []):
            if 'true_by_parallel' in cit:
                print("❌ FAIL: true_by_parallel field still present in cluster citations")
                break
        else:
            continue
        break
    else:
        print("✅ PASS: true_by_parallel field removed from cluster citations")

if __name__ == "__main__":
    asyncio.run(test_clustering_fixes())
