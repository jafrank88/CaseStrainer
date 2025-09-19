#!/usr/bin/env python3
"""
Test large document processing consistency.
"""

import requests
import time

def test_large_doc_multiple_times():
    """Test large document processing multiple times to check consistency."""
    
    # Test document with known citations
    test_text = """
    Legal Document Consistency Test
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """ + "\n\nAdditional content. " * 1000  # Make it large
    
    print("🔄 Testing Large Document Processing Consistency")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
    print()
    
    results = []
    
    for attempt in range(3):
        print(f"🧪 Attempt {attempt + 1}/3")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_text},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                citations_count = len(data.get('citations', []))
                processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
                success = data.get('success', False)
                
                result = {
                    'attempt': attempt + 1,
                    'success': success,
                    'citations': citations_count,
                    'mode': processing_mode,
                    'status': 'completed'
                }
                
                print(f"  ✅ Success: {success}")
                print(f"  📊 Citations: {citations_count}")
                print(f"  🔧 Mode: {processing_mode}")
                
            else:
                result = {
                    'attempt': attempt + 1,
                    'success': False,
                    'citations': 0,
                    'mode': 'api_error',
                    'status': f'HTTP {response.status_code}'
                }
                print(f"  ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            result = {
                'attempt': attempt + 1,
                'success': False,
                'citations': 0,
                'mode': 'exception',
                'status': str(e)
            }
            print(f"  💥 Exception: {e}")
        
        results.append(result)
        
        # Wait between attempts
        if attempt < 2:
            print("  ⏳ Waiting 2 seconds...")
            time.sleep(2)
    
    # Analyze results
    print("\n📊 CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    successful_attempts = [r for r in results if r['success']]
    citation_counts = [r['citations'] for r in results]
    processing_modes = [r['mode'] for r in results]
    
    print(f"Successful attempts: {len(successful_attempts)}/3")
    print(f"Citation counts: {citation_counts}")
    print(f"Processing modes: {processing_modes}")
    
    if len(set(citation_counts)) == 1:
        print("✅ Citation counts are consistent")
    else:
        print("❌ Citation counts are inconsistent")
    
    if len(set(processing_modes)) == 1:
        print("✅ Processing modes are consistent")
    else:
        print("❌ Processing modes are inconsistent")
    
    # Check if we have the expected sync_fallback mode
    if 'sync_fallback' in processing_modes:
        print("✅ Sync fallback is working")
    else:
        print("❌ Sync fallback is not working")
    
    return results

def main():
    """Run consistency test."""
    results = test_large_doc_multiple_times()
    
    # Summary
    if all(r['success'] for r in results) and all(r['citations'] > 0 for r in results):
        print("\n🎉 LARGE DOCUMENT PROCESSING IS WORKING CONSISTENTLY")
    else:
        print("\n⚠️ LARGE DOCUMENT PROCESSING HAS ISSUES")

if __name__ == "__main__":
    main()
