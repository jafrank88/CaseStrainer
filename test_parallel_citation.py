#!/usr/bin/env python3
"""
Test with parallel citations to verify the unified pipeline's parallel verification
"""

import requests
import json
import time

def test_parallel_citation():
    """Test with parallel citations that should trigger parallel verification"""
    
    # Use the Gresser case which has parallel citations
    test_text = "Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059."
    
    print("🧪 Testing Parallel Citation Detection")
    print(f"Test text: {test_text}")
    print()
    
    # Call the API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "type": "text",
        "text": test_text,
        "options": {
            "extract_case_names": True,
            "extract_dates": True,
            "verify_citations": True
        }
    }
    
    print("📡 Sending request to API...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=data, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"📥 Response received in {elapsed:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📊 Results Analysis:")
            print(f"✅ Success: {result.get('success')}")
            
            # Check nested result structure
            result_data = result.get('result', {})
            citations = result_data.get('citations', [])
            clusters = result_data.get('clusters', [])
            
            print(f"📄 Citations found: {len(citations)}")
            print(f"🔗 Clusters found: {len(clusters)}")
            
            # Check if unified pipeline was used
            metadata = result.get('metadata', {})
            processing_strategy = metadata.get('processing_strategy')
            processing_path = metadata.get('processing_path')
            print(f"🛤️  Processing strategy: {processing_strategy}")
            print(f"🛤️  Processing path: {processing_path}")
            
            if processing_strategy == 'unified_processing_pipeline':
                print("✅ UNIFIED PROCESSING STRATEGY IS BEING USED!")
            elif processing_path == 'unified_pipeline':
                print("✅ UNIFIED PIPELINE IS BEING USED!")
            else:
                print("⚠️  Unified pipeline not detected - using fallback")
            
            # Check parallel verification
            parallel_count = sum(1 for c in citations if c.get('true_by_parallel', False))
            print(f"🔄 Parallel verifications: {parallel_count}")
            
            # Show citation details
            print("\n📋 Citation Details:")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.get('citation')}")
                print(f"     Verified: {cit.get('verified')}")
                print(f"     True by parallel: {cit.get('true_by_parallel')}")
                print(f"     Extracted case name: {cit.get('extracted_case_name')}")
                print(f"     Canonical name: {cit.get('canonical_name')}")
                print(f"     Cluster ID: {cit.get('cluster_id')}")
                print()
            
            # Check for pipeline metadata
            if 'parallel_verifications' in metadata:
                print(f"📈 Pipeline metadata: {metadata.get('parallel_verifications')} parallel verifications applied")
            
            return len(citations) > 0
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_parallel_citation()
    if success:
        print("\n🎉 Parallel citation test PASSED!")
    else:
        print("\n💥 Parallel citation test FAILED!")
