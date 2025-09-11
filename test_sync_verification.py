#!/usr/bin/env python3
"""
Test verification synchronously without RQ queue to verify the logic works.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_sync_verification():
    """Test verification logic synchronously."""
    print("🧪 Testing Synchronous Verification (No RQ Queue)")
    print("=" * 60)
    
    try:
        # Import the verification function directly
        from src.async_verification_worker import verify_citations_enhanced
        
        # Test paragraph with parallel citations
        test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
        
        print(f"📝 Test Text:")
        print(f"   {test_text[:100]}...")
        print()
        
        # Create test citations
        test_citations = [
            {
                'citation': '200 Wn.2d 72',
                'extracted_case_name': 'Convoyant, LLC v. DeepThink, LLC',
                'extracted_date': '2022',
                'confidence_score': 0.7,
                'extraction_method': 'unified_processor'
            },
            {
                'citation': '514 P.3d 643',
                'extracted_case_name': 'Convoyant, LLC v. DeepThink, LLC',
                'extracted_date': '2022',
                'confidence_score': 0.7,
                'extraction_method': 'unified_processor'
            }
        ]
        
        print(f"🔍 Testing verification for {len(test_citations)} citations...")
        
        # Call verification function directly
        result = verify_citations_enhanced(
            citations=test_citations,
            text=test_text,
            request_id="test_sync_001",
            input_type="text",
            metadata={}
        )
        
        print("✅ Verification completed!")
        print()
        
        # Display results
        print("📊 VERIFICATION RESULTS:")
        print("=" * 60)
        print(f"Success: {result.get('success', 'N/A')}")
        print(f"Verification Method: {result.get('verification_method', 'N/A')}")
        print(f"Processing Time: {result.get('processing_time', 'N/A')}")
        print(f"Citations Processed: {len(result.get('citations', []))}")
        
        if 'citations' in result:
            for i, citation in enumerate(result['citations'], 1):
                print(f"\n🔍 Citation {i}: {citation.get('citation', 'N/A')}")
                print(f"   📝 Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"   📅 Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"   🎯 Canonical Case Name: {citation.get('canonical_name', 'N/A')}")
                print(f"   📅 Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"   🔗 Canonical URL: {citation.get('canonical_url', 'N/A')}")
                print(f"   ✅ Verified: {citation.get('verified', 'N/A')}")
                print(f"   📚 Source: {citation.get('verification_source', 'N/A')}")
                print(f"   🎯 Confidence: {citation.get('confidence', 'N/A')}")
        
        if 'quality_metrics' in result:
            print(f"\n📈 Quality Metrics:")
            print(json.dumps(result['quality_metrics'], indent=2, default=str))
        
        print(f"\n🔍 FULL RESULT:")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Synchronous verification test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_verification()
