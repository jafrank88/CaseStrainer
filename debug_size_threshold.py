#!/usr/bin/env python3
"""
Debug the size threshold logic to see why large documents aren't going async.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_size_threshold():
    """Test the size threshold logic directly."""
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        
        # Test different sizes
        test_cases = [
            ("Small text", "Short citation test with State v. Smith, 150 Wn.2d 674.", "sync"),
            ("Medium text", "A" * 1500 + " State v. Johnson, 160 Wn.2d 500.", "sync"),  # 1.5KB
            ("Large text", "B" * 3000 + " City v. Williams, 170 Wn.2d 200.", "async"),  # 3KB
            ("Very large", "C" * 10000 + " Brown v. State, 180 Wn.2d 300.", "async")   # 10KB
        ]
        
        print("🧪 Testing Size Threshold Logic")
        print("=" * 50)
        print("Threshold: 2KB (2048 bytes)")
        print()
        
        for name, text, expected in test_cases:
            size_bytes = len(text.encode('utf-8'))
            size_kb = size_bytes / 1024
            
            input_data = {'type': 'text', 'text': text}
            should_process_immediately = service.should_process_immediately(input_data)
            
            actual = "sync" if should_process_immediately else "async"
            status = "✅" if actual == expected else "❌"
            
            print(f"{status} {name}:")
            print(f"    Size: {size_bytes} bytes ({size_kb:.1f} KB)")
            print(f"    Expected: {expected}, Actual: {actual}")
            print(f"    Should process immediately: {should_process_immediately}")
            print()
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_size_threshold()
