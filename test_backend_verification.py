#!/usr/bin/env python3
"""
Test the backend verification process through the enhanced sync processor.
This will test the complete pipeline including citation extraction, verification, and clustering.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_sync_processor import EnhancedSyncProcessor

def test_backend_verification():
    """Test the complete backend verification process."""
    print("🧪 Testing Backend Verification Process")
    print("=" * 60)
    
    # Initialize the enhanced sync processor
    processor = EnhancedSyncProcessor()
    
    # Test paragraph with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"📝 Test Text:")
    print(f"   {test_text[:100]}...")
    print()
    
    # Process the text through the enhanced sync processor
    print("🔄 Processing text through Enhanced Sync Processor...")
    
    try:
        # Use the enhanced sync processor
        result = processor.process_any_input_enhanced(
            input_data=test_text,
            input_type="text",
            options={
                "enable_enhanced_verification": True,
                "enable_clustering": True,
                "request_id": "test_verification_001"
            }
        )
        
        print("✅ Processing completed successfully!")
        print()
        
        # Display the results
        print("📊 PROCESSING RESULTS:")
        print("=" * 60)
        
        # Check if we have citations
        if 'citations' in result:
            citations = result['citations']
            print(f"📋 Found {len(citations)} citations")
            print()
            
            # Display each citation with its metadata
            for i, citation in enumerate(citations, 1):
                print(f"🔍 Citation {i}: {citation.get('citation', 'N/A')}")
                print(f"   📝 Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"   📅 Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"   🎯 Canonical Case Name: {citation.get('canonical_name', 'N/A')}")
                print(f"   📅 Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"   🔗 Canonical URL: {citation.get('canonical_url', 'N/A')}")
                print(f"   📚 Source: {citation.get('source', 'N/A')}")
                print(f"   ✅ Verified: {citation.get('verified', 'N/A')}")
                print(f"   🎯 Confidence: {citation.get('confidence_score', 'N/A')}")
                print(f"   🏷️  Extraction Method: {citation.get('extraction_method', 'N/A')}")
                print()
        
        # Check if we have clusters
        if 'clusters' in result:
            clusters = result['clusters']
            print(f"🎯 Found {len(clusters)} clusters")
            print()
            
            for i, cluster in enumerate(clusters, 1):
                print(f"📦 Cluster {i}: {cluster.get('case_name', 'N/A')} ({cluster.get('year', 'N/A')})")
                print(f"   📊 Size: {cluster.get('size', 'N/A')} citations")
                print(f"   🏷️  Type: {cluster.get('cluster_type', 'N/A')}")
                print(f"   🎯 Citations: {', '.join(cluster.get('citations', []))}")
                print()
        
        # Display full result structure
        print("🔍 FULL RESULT STRUCTURE:")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend_verification()
