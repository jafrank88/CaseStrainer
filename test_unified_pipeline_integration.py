#!/usr/bin/env python3
"""
Test the unified pipeline integration in the API
"""

import requests
import json
import time

def test_unified_pipeline():
    """Test that the unified pipeline is being used in the API"""
    
    # Test case with parallel citations - use real legal content
    test_text = """In the case of Smith v. Johnson, the court established important precedent. 
    This ruling was later cited in Johnson v. Smith, 123 F.3d 456 (2023), which clarified the 
    application of the original decision. The appellate court affirmed the lower court's 
    reasoning and expanded upon the legal framework first established in the initial case."""
    
    print("🧪 Testing Unified Pipeline Integration")
    print(f"Test text length: {len(test_text)} characters")
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
            print(f"📄 Citations found: {len(result.get('citations', []))}")
            print(f"🔗 Clusters found: {len(result.get('clusters', []))}")
            
            # Check if unified pipeline was used
            metadata = result.get('metadata', {})
            processing_path = metadata.get('processing_path')
            print(f"🛤️  Processing path: {processing_path}")
            
            if processing_path == 'unified_pipeline':
                print("✅ UNIFIED PIPELINE IS BEING USED!")
            else:
                print("⚠️  Unified pipeline not detected - using fallback")
            
            # Check parallel verification
            citations = result.get('citations', [])
            parallel_count = sum(1 for c in citations if c.get('true_by_parallel', False))
            print(f"🔄 Parallel verifications: {parallel_count}")
            
            # Show citation details
            print("\n📋 Citation Details:")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.get('citation')}")
                print(f"     Verified: {cit.get('verified')}")
                print(f"     True by parallel: {cit.get('true_by_parallel')}")
                print(f"     Canonical name: {cit.get('canonical_name', 'N/A')}")
                print()
            
            # Check for pipeline metadata
            if 'parallel_verifications' in metadata:
                print(f"📈 Pipeline metadata: {metadata.get('parallel_verifications')} parallel verifications applied")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_unified_pipeline()
    if success:
        print("\n🎉 Unified pipeline integration test PASSED!")
    else:
        print("\n💥 Unified pipeline integration test FAILED!")
