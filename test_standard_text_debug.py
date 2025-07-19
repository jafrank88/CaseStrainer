#!/usr/bin/env python3
"""
Debug test for standard text processing
"""

import requests
import time

def test_standard_text_debug():
    """Debug why standard text is still slow"""
    print("🔍 Standard Text Debug")
    print("=" * 40)
    
    # Standard text that's timing out
    standard_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"Standard text: {len(standard_text)} chars, {len(standard_text.split())} words")
    print(f"Text preview: {standard_text[:100]}...")
    
    test_data = {
        "text": standard_text,
        "source_type": "text"
    }
    
    # Test with different timeouts to see where it's getting stuck
    timeouts = [2, 5, 10, 15]
    
    for timeout in timeouts:
        print(f"\n--- Testing with {timeout} second timeout ---")
        
        try:
            start_time = time.time()
            response = requests.post(
                "https://wolf.law.uw.edu/casestrainer/api/analyze",
                json=test_data,
                timeout=timeout
            )
            processing_time = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get('metadata', {})
                print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
                print(f"Processor: {metadata.get('processor_used', 'N/A')}")
                print(f"Task type: {metadata.get('task_type', 'N/A')}")
                
                citations = result.get('citations', [])
                print(f"Found {len(citations)} citations")
                
                if processing_time < timeout:
                    print(f"🎉 Completed in {processing_time:.2f} seconds")
                    break
                else:
                    print(f"⚠️  Slow: {processing_time:.2f} seconds")
                    
            else:
                print(f"❌ Error: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ TIMEOUT after {timeout} seconds")
            print("The processing is getting stuck somewhere...")
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "="*40)
    print("Debug complete!")

if __name__ == "__main__":
    test_standard_text_debug() 