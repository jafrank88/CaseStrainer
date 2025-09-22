#!/usr/bin/env python3
"""
Debug verification to see why citations aren't being verified.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_verification_debug():
    """Debug verification settings."""
    
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    
    print("🔍 VERIFICATION DEBUG")
    print("=" * 60)
    print(f"📝 Text: {text}")
    print(f"📏 Text length: {len(text)} characters")
    print()
    
    # Check if verification would be enabled based on text length
    enable_verification = len(text) > 500
    print(f"🔧 Verification enabled by length (>500): {enable_verification}")
    
    # Check if there are Washington citations
    has_wn_citations = 'Wn.' in text
    print(f"🏛️  Has Washington citations: {has_wn_citations}")
    
    if has_wn_citations:
        enable_verification = True
        print(f"🔧 Verification enabled by WA citations: {enable_verification}")
    
    print()
    print(f"🎯 Final verification setting: {enable_verification}")
    
    # Test the unified clustering directly
    try:
        from src.unified_citation_clustering import cluster_citations_unified
        
        print()
        print("🧪 Testing unified clustering with verification enabled...")
        
        # Create mock citations
        mock_citations = [
            {'citation': '578 U.S. 330', 'extracted_case_name': 'Spokeo, Inc. v. Robins', 'extracted_date': '2016'},
            {'citation': '521 U.S. 811', 'extracted_case_name': 'Raines v. Byrd', 'extracted_date': '1997'},
            {'citation': '117 S. Ct. 2312', 'extracted_case_name': 'Raines v. Byrd', 'extracted_date': '1997'},
            {'citation': '138 L. Ed. 2d 849', 'extracted_case_name': 'Raines v. Byrd', 'extracted_date': '1997'}
        ]
        
        result = cluster_citations_unified(
            mock_citations,
            text,
            enable_verification=True  # Force verification
        )
        
        print(f"📊 Clustering result: {len(result)} clusters")
        
        for i, cluster in enumerate(result, 1):
            print(f"\n{i}. Cluster: {cluster.get('case_name', 'N/A')}")
            citations = cluster.get('citations', [])
            print(f"   Citations: {len(citations)}")
            
            for cit in citations:
                citation_text = cit.get('citation', 'N/A') if isinstance(cit, dict) else str(cit)
                verified = cit.get('verified', False) if isinstance(cit, dict) else False
                true_by_parallel = cit.get('true_by_parallel', False) if isinstance(cit, dict) else False
                
                print(f"   - {citation_text}: verified={verified}, true_by_parallel={true_by_parallel}")
        
    except Exception as e:
        print(f"❌ Error testing clustering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_debug()
