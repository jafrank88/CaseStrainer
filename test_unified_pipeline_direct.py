#!/usr/bin/env python3
"""
Test the unified pipeline directly to see why it's failing in the API
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_processing_pipeline import process_citations_unified

async def test_unified_pipeline_direct():
    """Test the unified pipeline directly"""
    
    # Use a simple test case
    test_text = "This is clearly established in Smith v. Jones, 123 F.3d 456 (9th Cir. 2023)."
    
    print("🧪 Testing Unified Pipeline Directly")
    print(f"Test text: {test_text}")
    print()
    
    try:
        print("📡 Calling unified pipeline directly...")
        result = await process_citations_unified(test_text, enable_parallel_verification=True)
        
        print("✅ Unified pipeline completed successfully!")
        print(f"📄 Citations found: {len(result.get('citations', []))}")
        print(f"🔗 Clusters found: {len(result.get('clusters', []))}")
        
        # Check metadata
        metadata = result.get('metadata', {})
        print(f"🛤️  Processing path: {metadata.get('processing_path')}")
        print(f"🔄 Parallel verifications: {metadata.get('parallel_verifications', 0)}")
        
        # Show citations
        citations = result.get('citations', [])
        print("\n📋 Citation Details:")
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.get('citation')}")
            print(f"     Verified: {cit.get('verified')}")
            print(f"     True by parallel: {cit.get('true_by_parallel')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Unified pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_unified_pipeline_direct())
    if success:
        print("\n🎉 Unified pipeline direct test PASSED!")
    else:
        print("\n💥 Unified pipeline direct test FAILED!")
