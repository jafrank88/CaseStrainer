"""
Simple Deduplication Test
Quick test to see if deduplication is being called.
"""

import requests
import json

def test_simple():
    """Simple test with minimal text."""
    
    print("🔍 SIMPLE DEDUPLICATION TEST")
    print("=" * 30)
    
    # Simple text with known duplicates
    test_text = """Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)
Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)"""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text: {test_text}")
    print(f"📏 Length: {len(test_text)} characters")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            processing_strategy = result.get('result', {}).get('metadata', {}).get('processing_strategy', 'unknown')
            
            print(f"✅ Response received")
            print(f"   Processing strategy: {processing_strategy}")
            print(f"   Citations found: {len(citations)}")
            
            # Check for duplicates
            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
            unique_citations = set(citation_texts)
            duplicates = len(citation_texts) - len(unique_citations)
            
            print(f"   Duplicates: {duplicates}")
            
            if duplicates == 0:
                print(f"   ✅ NO DUPLICATES!")
            else:
                print(f"   ❌ {duplicates} DUPLICATES FOUND!")
                from collections import Counter
                counts = Counter(citation_texts)
                for citation, count in counts.items():
                    if count > 1:
                        print(f"      '{citation}' appears {count} times")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple()
