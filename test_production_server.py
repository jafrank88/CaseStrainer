#!/usr/bin/env python3
"""
Comprehensive test of the production server
"""

import requests
import time
import json

def test_production_server():
    """Test the production server comprehensively"""
    print("🏭 Production Server Test")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("Production Server", "https://wolf.law.uw.edu/casestrainer/api/analyze"),
        ("Health Check", "https://wolf.law.uw.edu/casestrainer/api/health")
    ]
    
    # Test with simple text
    test_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    print(f"Test text: {test_text}")
    print(f"Length: {len(test_text)} chars, {len(test_text.split())} words")
    
    test_data = {
        "text": test_text,
        "source_type": "text"
    }
    
    for name, url in endpoints:
        print(f"\n{'='*20} {name} {'='*20}")
        print(f"URL: {url}")
        
        try:
            print("Sending request...")
            start_time = time.time()
            
            if "health" in url.lower():
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=test_data, timeout=10)
            
            processing_time = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                if "health" in url.lower():
                    print("✅ Health check successful")
                    try:
                        health_data = response.json()
                        print(f"Health data: {health_data}")
                    except:
                        print(f"Health response: {response.text[:200]}")
                else:
                    try:
                        result = response.json()
                        metadata = result.get('metadata', {})
                        print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
                        print(f"Processor used: {metadata.get('processor_used', 'N/A')}")
                        print(f"Task type: {metadata.get('task_type', 'N/A')}")
                        
                        # Show citations found
                        citations = result.get('citations', [])
                        print(f"Found {len(citations)} citations:")
                        for i, citation in enumerate(citations, 1):
                            print(f"  {i}. {citation.get('citation', 'N/A')}")
                            print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                            print(f"     Date: {citation.get('extracted_date', 'N/A')}")
                            print(f"     Canonical: {citation.get('canonical_name', 'N/A')} ({citation.get('canonical_date', 'N/A')})")
                        
                        # Check if it was fast
                        if processing_time < 2.0:
                            print(f"🎉 SUCCESS: Processing completed in {processing_time:.2f} seconds (under 2 seconds)")
                        else:
                            print(f"⚠️  WARNING: Processing took {processing_time:.2f} seconds (over 2 seconds)")
                            
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON response: {response.text[:200]}...")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed")
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "="*60)
    
    # Test with standard text to see if it's still slow
    print("Testing with standard text...")
    standard_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    test_data = {
        "text": standard_text,
        "source_type": "text"
    }
    
    try:
        print("Sending standard text request (5 second timeout)...")
        start_time = time.time()
        
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            json=test_data,
            timeout=5
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
            print(f"Found {len(citations)} citations:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
                print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Date: {citation.get('extracted_date', 'N/A')}")
                print(f"     Canonical: {citation.get('canonical_name', 'N/A')} ({citation.get('canonical_date', 'N/A')})")
            
            if processing_time < 5.0:
                print(f"🎉 SUCCESS: Standard text processed in {processing_time:.2f} seconds")
            else:
                print(f"⚠️  WARNING: Standard text still slow: {processing_time:.2f} seconds")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 5 seconds")
        print("❌ Standard text is still processing slowly")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_production_server() 