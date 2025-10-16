#!/usr/bin/env python3

import requests
import json

def simple_pdf_routing_test():
    """Simple test to check routing with different text sizes."""
    
    print("🔄 SIMPLE PDF ROUTING TEST")
    print("=" * 50)
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test cases with different sizes
    test_cases = [
        {
            'name': 'Small Text',
            'text': 'State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022).',
            'expected': 'sync'
        },
        {
            'name': 'Medium Text (4KB)',
            'text': ('State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). ' * 70),
            'expected': 'sync'
        },
        {
            'name': 'Large Text (6KB)',
            'text': ('State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). ' * 100),
            'expected': 'async'
        }
    ]
    
    # Add PDF text if available
    try:
        with open("extracted_pdf_text.txt", "r", encoding="utf-8") as f:
            pdf_text = f.read()
        
        test_cases.append({
            'name': 'PDF Text (66KB)',
            'text': pdf_text,
            'expected': 'async'
        })
    except FileNotFoundError:
        print("⚠️  PDF text not available, skipping PDF test")
    
    results = []
    
    for test_case in test_cases:
        name = test_case['name']
        text = test_case['text']
        expected = test_case['expected']
        size = len(text)
        
        print(f"\n🧪 Testing: {name}")
        print(f"   Size: {size:,} bytes")
        print(f"   Expected: {expected}")
        
        data = {"text": text, "type": "text"}
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                task_id = result.get('task_id')
                processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
                citations_count = len(result.get('citations', []))
                
                if task_id:
                    actual = 'async'
                    print(f"   Result: ASYNC (queued) - Task ID: {task_id}")
                else:
                    actual = 'sync'
                    print(f"   Result: SYNC ({processing_mode}) - {citations_count} citations")
                
                correct = actual == expected
                status = "✅" if correct else "❌"
                print(f"   Status: {status} {'CORRECT' if correct else 'INCORRECT'}")
                
                results.append({
                    'name': name,
                    'size': size,
                    'expected': expected,
                    'actual': actual,
                    'correct': correct,
                    'citations': citations_count,
                    'task_id': task_id
                })
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Summary
    print(f"\n📊 ROUTING TEST SUMMARY:")
    print("=" * 30)
    
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    
    for result in results:
        status = "✅" if result['correct'] else "❌"
        print(f"   {result['name']:15}: {result['size']:>8,} bytes → {result['expected']:5} vs {result['actual']:5} {status}")
    
    print(f"\n   Accuracy: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
    
    if correct_count == total_count:
        print("🎉 All routing decisions are correct!")
    else:
        print("⚠️  Some routing decisions are incorrect")
        
        # Identify the issues
        incorrect = [r for r in results if not r['correct']]
        for result in incorrect:
            print(f"   Issue: {result['name']} ({result['size']:,} bytes) expected {result['expected']} but got {result['actual']}")
    
    # Check for the specific PDF issue
    pdf_results = [r for r in results if 'PDF' in r['name']]
    if pdf_results:
        pdf_result = pdf_results[0]
        print(f"\n🔍 PDF SPECIFIC ANALYSIS:")
        print(f"   Size: {pdf_result['size']:,} bytes (should be > 5,120 for async)")
        print(f"   Expected: {pdf_result['expected']}")
        print(f"   Actual: {pdf_result['actual']}")
        
        if pdf_result['actual'] == 'sync' and pdf_result['size'] > 5120:
            print("   🚨 ISSUE: Large PDF processed as sync instead of async")
            print("   This suggests a routing logic problem")
        elif pdf_result['actual'] == 'sync' and pdf_result['citations'] == 0:
            print("   🚨 ISSUE: No citations found in PDF")
            print("   This suggests a processing problem")

if __name__ == "__main__":
    simple_pdf_routing_test()
