#!/usr/bin/env python3
"""
Quick test to verify the processing delay fix
"""

import requests
import time

def test_quick_fix():
    """Test if the processing delay fix is working"""
    print("🔧 Quick Fix Test")
    print("=" * 30)
    
    # Test with simple text
    test_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    test_data = {
        "text": test_text,
        "source_type": "text"
    }
    
    print(f"Testing simple text ({len(test_text)} chars, {len(test_text.split())} words)")
    print(f"Text: {test_text}")
    
    try:
        print("\nSending request to Docker backend (port 5001)...")
        start_time = time.time()
        
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            json=test_data,
            timeout=5  # 5 second timeout
        )
        
        processing_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Processing Time: {processing_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
            print(f"Processor used: {metadata.get('processor_used', 'N/A')}")
            
            # Show citations found
            citations = result.get('citations', [])
            print(f"\nFound {len(citations)} citations:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
                print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Date: {citation.get('extracted_date', 'N/A')}")
                print(f"     Canonical: {citation.get('canonical_name', 'N/A')} ({citation.get('canonical_date', 'N/A')})")
            
            # Check if it was fast
            if processing_time < 2.0:
                print(f"\n🎉 SUCCESS: Processing completed in {processing_time:.2f} seconds (under 2 seconds)")
            else:
                print(f"\n⚠️  WARNING: Processing took {processing_time:.2f} seconds (over 2 seconds)")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 5 seconds")
        print("❌ The processing delay fix may not be working")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Production server may not be accessible")
        print("Try running: .\\cslaunch.ps1 -Mode Production -QuickStart")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_quick_fix() 