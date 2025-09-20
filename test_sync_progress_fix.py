#!/usr/bin/env python3
"""
Test the sync progress bar fix.
This test verifies that:
1. The /processing_progress endpoint exists and works
2. Sync processing returns processing_mode = 'immediate'
3. Progress data is included in sync responses
"""

import requests
import time
import json

def test_processing_progress_endpoint():
    """Test that the processing_progress endpoint works."""
    
    print("📊 Testing Processing Progress Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(
            "http://localhost:8080/casestrainer/api/processing_progress",
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ Endpoint failed: {response.status_code}")
            return False
        
        data = response.json()
        
        print(f"📊 Progress Endpoint Response:")
        print(f"   Status: {data.get('status')}")
        print(f"   Current Step: {data.get('current_step')}")
        print(f"   Progress: {data.get('progress')}%")
        print(f"   Message: {data.get('message')}")
        print(f"   Processing Mode: {data.get('processing_mode')}")
        
        # Check required fields
        required_fields = ['status', 'current_step', 'progress', 'message']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print(f"✅ Processing progress endpoint working correctly")
        return True
        
    except Exception as e:
        print(f"💥 Processing progress endpoint test failed: {e}")
        return False

def test_sync_processing_mode():
    """Test that sync processing returns the correct processing mode."""
    
    print(f"\n🔄 Testing Sync Processing Mode")
    print("=" * 50)
    
    # Small document that should trigger sync processing
    test_text = """
    Legal Document
    
    State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) was important.
    City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) followed.
    """
    
    try:
        print("📤 Submitting small document for sync processing...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check processing mode
        processing_mode = data.get('metadata', {}).get('processing_mode')
        progress_data = data.get('progress_data')
        
        print(f"📊 Sync Processing Results:")
        print(f"   Processing Mode: {processing_mode}")
        print(f"   Success: {data.get('success')}")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Progress Data Present: {progress_data is not None}")
        
        if progress_data:
            print(f"   Progress Steps: {len(progress_data.get('steps', []))}")
            print(f"   Total Progress: {progress_data.get('total_progress', 0)}%")
        
        # Verify processing mode
        if processing_mode != 'immediate':
            print(f"❌ Expected processing_mode='immediate', got '{processing_mode}'")
            return False
        
        # Verify progress data is included
        if not progress_data:
            print(f"❌ No progress data in sync response")
            return False
        
        print(f"✅ Sync processing mode and progress data working correctly")
        return True
        
    except Exception as e:
        print(f"💥 Sync processing mode test failed: {e}")
        return False

def test_sync_progress_integration():
    """Test the complete sync progress integration."""
    
    print(f"\n🎯 Testing Complete Sync Progress Integration")
    print("=" * 50)
    
    print("1. Testing processing_progress endpoint...")
    endpoint_ok = test_processing_progress_endpoint()
    
    print("\n2. Testing sync processing mode...")
    mode_ok = test_sync_processing_mode()
    
    success = endpoint_ok and mode_ok
    
    print(f"\n🎯 Sync Progress Integration: {'✅ WORKING' if success else '❌ NEEDS WORK'}")
    
    if success:
        print("✅ Frontend should now be able to:")
        print("   - Poll /processing_progress for sync operations")
        print("   - Detect processing_mode='immediate' in responses")
        print("   - Show progress bar and spinner during sync processing")
        print("   - Complete progress when sync processing finishes")
    else:
        print("❌ Some components of sync progress are not working")
    
    return success

def main():
    """Run sync progress fix tests."""
    
    print("🚀 Testing Sync Progress Bar Fix")
    print("=" * 60)
    
    success = test_sync_progress_integration()
    
    print("\n" + "=" * 60)
    print("📋 SYNC PROGRESS FIX TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 SYNC PROGRESS BAR FIX SUCCESSFUL!")
        print("✅ The progress bar and spinner should now work in sync mode")
        print("✅ Frontend can detect sync processing and show appropriate progress")
    else:
        print("⚠️ Sync progress bar fix needs additional work")
    
    return success

if __name__ == "__main__":
    main()
