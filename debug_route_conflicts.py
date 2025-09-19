#!/usr/bin/env python3
"""
Debug route conflicts by examining what routes are actually registered.
"""

import requests
import json

def debug_route_conflicts():
    """Debug route conflicts by checking what routes are actually registered."""
    
    print("🔍 Debugging Route Conflicts")
    print("=" * 60)
    
    # Test 1: Check what routes are registered
    print("🧪 Test 1: Checking Registered Routes")
    try:
        response = requests.get("http://localhost:8080/casestrainer/api/routes")
        
        if response.status_code == 200:
            data = response.json()
            routes = data.get('routes', [])
            
            print(f"  📊 Found {len(routes)} registered routes")
            
            # Look for analyze routes specifically
            analyze_routes = [r for r in routes if 'analyze' in r.get('rule', '')]
            
            print(f"  🔍 Analyze routes found: {len(analyze_routes)}")
            for route in analyze_routes:
                print(f"    - {route.get('rule')} [{', '.join(route.get('methods', []))}]")
                print(f"      Endpoint: {route.get('endpoint')}")
                if 'blueprint' in route:
                    print(f"      Blueprint: {route.get('blueprint')}")
                print()
            
            # Check for duplicate routes
            rules = [r.get('rule') for r in routes]
            analyze_rule = '/casestrainer/api/analyze'
            analyze_count = rules.count(analyze_rule)
            
            if analyze_count > 1:
                print(f"  ❌ ROUTE CONFLICT DETECTED: {analyze_rule} appears {analyze_count} times!")
                return False
            elif analyze_count == 1:
                print(f"  ✅ No route conflict: {analyze_rule} appears exactly once")
                return True
            else:
                print(f"  ⚠️ Route not found: {analyze_rule} not registered")
                return False
                
        else:
            print(f"  ❌ Could not fetch routes: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  💥 Route check failed: {e}")
        return False

def test_route_behavior():
    """Test the actual behavior of the analyze route."""
    
    print("\n🧪 Test 2: Testing Route Behavior")
    
    # Test with a small document first
    small_text = "Test document with State v. Johnson, 160 Wn.2d 500."
    
    print("  📝 Testing small document (should be sync)...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": small_text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            citations = len(data.get('citations', []))
            
            print(f"    Status: {response.status_code}")
            print(f"    Processing mode: {processing_mode}")
            print(f"    Citations: {citations}")
            print(f"    Has task_id: {'task_id' in data}")
            
            if processing_mode == 'immediate' and citations > 0:
                print("    ✅ Small document processing working correctly")
                small_working = True
            else:
                print("    ⚠️ Small document processing has issues")
                small_working = False
        else:
            print(f"    ❌ Small document failed: {response.status_code}")
            small_working = False
            
    except Exception as e:
        print(f"    💥 Small document test failed: {e}")
        small_working = False
    
    # Test with a large document
    large_text = "Test document with State v. Johnson, 160 Wn.2d 500." + "\n\nPadding. " * 1000
    
    print("\n  📄 Testing large document (should be async or sync_fallback)...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            citations = len(data.get('citations', []))
            success = data.get('success', False)
            
            print(f"    Status: {response.status_code}")
            print(f"    Processing mode: {processing_mode}")
            print(f"    Citations: {citations}")
            print(f"    Success: {success}")
            print(f"    Has task_id: {'task_id' in data}")
            
            if processing_mode == 'sync_fallback' and citations > 0:
                print("    ✅ Large document processing working correctly (sync fallback)")
                large_working = True
            elif processing_mode == 'queued' and 'task_id' in data:
                print("    ✅ Large document processing working correctly (async)")
                large_working = True
            elif processing_mode == 'queued' and citations == 0:
                print("    ❌ Large document stuck in 'queued' mode with no results")
                large_working = False
            else:
                print(f"    ⚠️ Large document processing unexpected: mode={processing_mode}, citations={citations}")
                large_working = False
        else:
            print(f"    ❌ Large document failed: {response.status_code}")
            large_working = False
            
    except Exception as e:
        print(f"    💥 Large document test failed: {e}")
        large_working = False
    
    return small_working, large_working

def check_blueprint_registration():
    """Check which blueprints are actually registered."""
    
    print("\n🧪 Test 3: Checking Blueprint Registration")
    
    try:
        # Try to access a Vue API specific endpoint
        response = requests.get("http://localhost:8080/casestrainer/api/health")
        
        if response.status_code == 200:
            print("    ✅ Vue API blueprint is accessible")
            return True
        else:
            print(f"    ❌ Vue API blueprint not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    💥 Blueprint check failed: {e}")
        return False

def investigate_response_headers():
    """Check response headers for clues about which handler is responding."""
    
    print("\n🧪 Test 4: Investigating Response Headers")
    
    test_text = "Test with State v. Johnson, 160 Wn.2d 500." + "\n\nPadding. " * 1000
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},
            timeout=30
        )
        
        print(f"    Response Headers:")
        for key, value in response.headers.items():
            print(f"      {key}: {value}")
        
        print(f"\n    Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Response Keys: {list(data.keys())}")
            print(f"    Processing Mode: {data.get('metadata', {}).get('processing_mode', 'N/A')}")
            
            # Look for clues about which handler processed this
            if 'job_id' in data.get('metadata', {}):
                print("    🔍 Contains job_id - likely from progress_manager")
            if 'request_id' in data:
                print("    🔍 Contains request_id - likely from vue_api_endpoints")
            
    except Exception as e:
        print(f"    💥 Header investigation failed: {e}")

def main():
    """Run all route conflict debugging tests."""
    
    print("🚀 Starting Route Conflict Investigation")
    print("=" * 60)
    
    # Run all tests
    routes_ok = debug_route_conflicts()
    small_ok, large_ok = test_route_behavior()
    blueprint_ok = check_blueprint_registration()
    investigate_response_headers()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 ROUTE CONFLICT INVESTIGATION SUMMARY")
    print("=" * 60)
    
    print(f"Routes Check: {'✅ PASS' if routes_ok else '❌ FAIL'}")
    print(f"Small Document: {'✅ PASS' if small_ok else '❌ FAIL'}")
    print(f"Large Document: {'✅ PASS' if large_ok else '❌ FAIL'}")
    print(f"Blueprint Access: {'✅ PASS' if blueprint_ok else '❌ FAIL'}")
    
    if routes_ok and small_ok and large_ok and blueprint_ok:
        print("\n🎉 NO ROUTE CONFLICTS DETECTED - System working correctly!")
    elif not routes_ok:
        print("\n❌ ROUTE CONFLICT CONFIRMED - Multiple handlers registered")
    elif not large_ok:
        print("\n⚠️ LARGE DOCUMENT ISSUE - Route conflict or processing problem")
    else:
        print("\n🔍 MIXED RESULTS - Further investigation needed")

if __name__ == "__main__":
    main()
