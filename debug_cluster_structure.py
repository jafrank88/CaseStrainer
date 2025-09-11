#!/usr/bin/env python3
"""
Debug script to inspect the actual structure of clusters returned by the backend
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def debug_cluster_structure():
    """Debug the cluster structure returned by the backend."""
    
    # Test text with 3 distinct cases
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is
substantial when sufficient to persuade a fair-minded person of the truth of the
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041
(2017). "Competent evidence sufficient to support the trial court's decision to
grant . . . a domestic violence protection order may contain hearsay or be wholly
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233
(2010)."""
    
    print("=== Debugging Cluster Structure ===")
    
    # Create processor
    processor = UnifiedCitationProcessorV2()
    
    # Process the text
    print("Processing text...")
    result = asyncio.run(processor.process_text(test_text))
    
    print(f"\nResult type: {type(result)}")
    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    if isinstance(result, dict):
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Clusters found: {len(result.get('clusters', []))}")
        
        # Inspect the first cluster in detail
        clusters = result.get('clusters', [])
        if clusters:
            print(f"\n=== First Cluster Details ===")
            first_cluster = clusters[0]
            print(f"Cluster type: {type(first_cluster)}")
            print(f"Cluster dir: {dir(first_cluster)}")
            
            # Try to get all attributes
            for attr in dir(first_cluster):
                if not attr.startswith('_'):
                    try:
                        value = getattr(first_cluster, attr)
                        if not callable(value):
                            print(f"  {attr}: {value}")
                    except Exception as e:
                        print(f"  {attr}: Error accessing - {e}")
            
            # Try common cluster attributes
            print(f"\n=== Common Cluster Attributes ===")
            common_attrs = ['case_name', 'year', 'citations', 'cluster_id', 'extracted_case_name', 'extracted_date']
            for attr in common_attrs:
                try:
                    value = getattr(first_cluster, attr, 'Attribute not found')
                    print(f"  {attr}: {value}")
                except Exception as e:
                    print(f"  {attr}: Error - {e}")
        
        # Also check if clusters might be in a different key
        print(f"\n=== All Result Keys and Types ===")
        for key, value in result.items():
            if isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
                if value:
                    print(f"    First item type: {type(value[0])}")
            else:
                print(f"  {key}: {type(value)}")
    
    return result

if __name__ == "__main__":
    debug_cluster_structure()



