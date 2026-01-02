#!/usr/bin/env python3
"""
Debug test to see exactly what's happening with the unified pipeline
"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

from src.unified_processing_pipeline import process_citations_unified

async def test_debug_unified_pipeline():
    """Debug test the unified pipeline"""
    
    # Use the Gresser parallel citation case
    test_text = "Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059."
    
    print("🧪 DEBUG: Testing Unified Pipeline Directly")
    print(f"Test text: {test_text}")
    print()
    
    try:
        print("📡 DEBUG: Calling unified pipeline directly...")
        result = await process_citations_unified(test_text, enable_parallel_verification=True)
        
        print("✅ DEBUG: Unified pipeline completed successfully!")
        print(f"📄 Citations found: {len(result.get('citations', []))}")
        print(f"🔗 Clusters found: {len(result.get('clusters', []))}")
        
        # Check metadata
        metadata = result.get('metadata', {})
        print(f"🛤️  DEBUG: Processing path: {metadata.get('processing_path')}")
        print(f"🔄 DEBUG: Parallel verifications: {metadata.get('parallel_verifications', 0)}")
        print(f"📊 DEBUG: All metadata keys: {list(metadata.keys())}")
        
        # Show citations
        citations = result.get('citations', [])
        print("\n📋 DEBUG: Citation Details:")
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.get('citation')}")
            print(f"     Verified: {cit.get('verified')}")
            print(f"     True by parallel: {cit.get('true_by_parallel')}")
            print(f"     Extracted case name: {cit.get('extracted_case_name')}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ DEBUG: Unified pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_debug_unified_pipeline())
    if result:
        print("\n🎉 DEBUG: Unified pipeline direct test completed!")
        print(f"🔍 DEBUG: Result type: {type(result)}")
        print(f"🔍 DEBUG: Result keys: {list(result.keys())}")
    else:
        print("\n💥 DEBUG: Unified pipeline direct test FAILED!")
