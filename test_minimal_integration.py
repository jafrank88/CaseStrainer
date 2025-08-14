#!/usr/bin/env python3
"""
Minimal Integration Test
Test the simplest possible integration to identify the core issue
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_minimal_integration():
    """Test minimal integration with very simple input."""
    print("🔍 MINIMAL INTEGRATION TEST")
    print("-" * 40)
    
    # Very simple test case
    simple_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        print("Step 1: Testing CitationService immediate processing...")
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': simple_text, 'type': 'text'}
        
        print(f"Input: {simple_text}")
        print(f"Should process immediately: {service.should_process_immediately(input_data)}")
        
        if service.should_process_immediately(input_data):
            result = service.process_immediately(input_data)
            print(f"Result: {result}")
            
            if result and result.get('status') == 'completed':
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                print(f"✅ Found {len(citations)} citations, {len(clusters)} clusters")
                
                if citations:
                    print("First citation details:")
                    for key, value in citations[0].items():
                        print(f"  {key}: {value}")
                
                return len(citations) > 0
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print("❌ Text not suitable for immediate processing")
            return False
        
    except Exception as e:
        print(f"❌ Minimal integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run minimal integration test."""
    print("🧪 MINIMAL INTEGRATION TEST")
    print("="*50)
    
    success = test_minimal_integration()
    
    print(f"\n" + "="*50)
    print("📊 MINIMAL INTEGRATION RESULTS")
    print("="*50)
    print(f"Minimal Integration: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
