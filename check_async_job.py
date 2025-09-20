#!/usr/bin/env python3
"""
Check the specific async job results.
"""

import requests
import json

def check_async_job():
    """Check the specific async job results."""
    
    print("🔍 Checking Async Job Results")
    print("=" * 50)
    
    job_id = "87c7a33e-2626-4592-b6a0-af1a9ca79d73"
    
    try:
        response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        print(f"📊 Async Job Results:")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Success: {data.get('success', False)}")
        
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"   Citations found: {len(citations)}")
        print(f"   Clusters found: {len(clusters)}")
        
        if len(citations) == 0:
            print(f"\n❌ PROBLEM: Async job completed but found no citations!")
            print(f"   This suggests an issue with the async processing pipeline")
            
            # Check if there's an error message
            error = data.get('error')
            if error:
                print(f"   Error: {error}")
            
            # Check metadata
            metadata = data.get('metadata', {})
            print(f"   Processing metadata: {json.dumps(metadata, indent=2)}")
            
            return False
        else:
            print(f"✅ Async job found citations successfully")
            
            # Show sample results
            print(f"\n📋 Sample Citations (first 3):")
            for i, citation in enumerate(citations[:3], 1):
                citation_text = citation.get('citation', 'N/A')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                verified = citation.get('verified', False)
                
                print(f"   {i}. '{citation_text}' → '{extracted_name}' (Verified: {verified})")
            
            return True
        
    except Exception as e:
        print(f"💥 Error checking async job: {e}")
        return False

def main():
    """Check the specific async job."""
    
    print("🚀 Async Job Status Check")
    print("=" * 60)
    
    success = check_async_job()
    
    print("\n" + "=" * 60)
    print("📋 ASYNC JOB DIAGNOSIS")
    print("=" * 60)
    
    if success:
        print("✅ Async processing is working correctly")
        print("🔧 Frontend Issue: The frontend is not polling for results")
        print("\n💡 Solutions:")
        print("   1. Frontend should poll /task_status/{job_id} until completed")
        print("   2. Check if frontend async polling logic is working")
        print("   3. Verify frontend displays results from completed async jobs")
    else:
        print("❌ Async processing pipeline has issues")
        print("🔧 Backend Issue: Async jobs complete but don't find citations")
        print("\n💡 Need to debug the async processing pipeline")
    
    return success

if __name__ == "__main__":
    main()
