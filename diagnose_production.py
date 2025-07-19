#!/usr/bin/env python3
"""
Simple diagnostic script for production server
"""

import requests
import time

def diagnose_production():
    """Diagnose the production server"""
    print("🔍 Production Server Diagnosis")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get("https://wolf.law.uw.edu/casestrainer/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Simple citation
    print("\n2. Testing simple citation...")
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
        "source_type": "text"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            json=test_data,
            timeout=10
        )
        processing_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {processing_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"   ✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
            print(f"   Processor: {metadata.get('processor_used', 'N/A')}")
            
            citations = result.get('citations', [])
            print(f"   Found {len(citations)} citations")
            
            if processing_time < 2.0:
                print("   🎉 FAST: Under 2 seconds")
            else:
                print("   ⚠️  SLOW: Over 2 seconds")
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            
    except requests.exceptions.Timeout:
        print("   ⏰ TIMEOUT: Request took too long")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check if adaptive learning is being used
    print("\n3. Checking for adaptive learning...")
    try:
        response = requests.get("https://wolf.law.uw.edu/casestrainer/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Health data: {health_data}")
            
            # Look for adaptive learning indicators
            if "adaptive" in str(health_data).lower():
                print("   ✅ Adaptive learning detected")
            else:
                print("   ❓ No adaptive learning indicators found")
    except Exception as e:
        print(f"   ❌ Error checking adaptive learning: {e}")
    
    print("\n" + "="*40)
    print("Diagnosis complete!")

if __name__ == "__main__":
    diagnose_production() 