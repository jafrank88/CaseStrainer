#!/usr/bin/env python3
"""
Test script to verify clustering works locally.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.services.citation_service import CitationService

def test_local_clustering():
    """Test local clustering with the same test data."""
    
    print("🧪 Testing local clustering...")
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    try:
        # Initialize citation service
        service = CitationService()
        
        # Test async processing (same as production)
        result = service.process_citation_task('test-clustering', 'text', {'text': test_text})
        
        print(f"📊 Result status: {result.get('status')}")
        print(f"📊 Citations: {len(result.get('citations', []))}")
        print(f"🔗 Clusters: {len(result.get('clusters', []))}")
        
        if result.get('clusters'):
            print("✅ SUCCESS: Clusters generated!")
            for i, cluster in enumerate(result['clusters']):
                print(f"   Cluster {i+1}: {cluster.get('canonical_name', 'N/A')} ({len(cluster.get('citations', []))} citations)")
        else:
            print("❌ FAILURE: No clusters generated")
            print(f"Full result keys: {list(result.keys())}")
            
        return len(result.get('clusters', [])) > 0
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_local_clustering()
    sys.exit(0 if success else 1) 