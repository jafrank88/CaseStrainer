#!/usr/bin/env python3
"""
Test the verification process step by step to identify where it's failing.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_sync_processor import EnhancedSyncProcessor

def test_verification_step_by_step():
    """Test the verification process step by step."""
    print("🧪 Testing Verification Process Step by Step")
    print("=" * 60)
    
    # Set Redis URL
    os.environ['REDIS_URL'] = 'redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0'
    
    # Initialize the enhanced sync processor
    processor = EnhancedSyncProcessor()
    
    # Test paragraph with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"📝 Test Text:")
    print(f"   {test_text[:100]}...")
    print()
    
    try:
        # Step 1: Extract citations
        print("🔍 Step 1: Extracting citations...")
        citations = processor._extract_citations_fast(test_text)
        print(f"✅ Found {len(citations)} citations")
        
        # Step 2: Extract names and years
        print("\n🔍 Step 2: Extracting names and years...")
        enhanced_citations = processor._extract_names_years_local(citations, test_text)
        print(f"✅ Enhanced {len(enhanced_citations)} citations")
        
        # Step 3: Cluster citations
        print("\n🔍 Step 3: Clustering citations...")
        clusters = processor._cluster_citations_local(enhanced_citations, test_text, "test_step_by_step")
        print(f"✅ Created {len(clusters)} clusters")
        
        # Step 4: Test verification queue
        print("\n🔍 Step 4: Testing verification queue...")
        try:
            # Try to queue verification
            verification_result = processor._queue_async_verification(
                enhanced_citations, 
                test_text, 
                "test_step_by_step", 
                "text", 
                {}
            )
            print(f"✅ Verification queued: {verification_result}")
        except Exception as e:
            print(f"❌ Verification queue failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ Step-by-step test completed!")
        print(f"   📊 Citations: {len(enhanced_citations)}")
        print(f"   🎯 Clusters: {len(clusters)}")
        
    except Exception as e:
        print(f"❌ Step-by-step test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_step_by_step()
