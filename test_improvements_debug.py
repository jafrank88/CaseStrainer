#!/usr/bin/env python3
"""
Quick test to see if improvements are being applied in production
"""

import sys
import os
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_improvements_debug():
    """Test if improvements are being applied"""
    
    print("🔍 TESTING IF IMPROVEMENTS ARE BEING APPLIED")
    print("=" * 50)
    
    # Test with a simple text that should trigger improvements
    test_text = "In Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 25 P.3d 512 (2001), the court held that environmental regulations apply. Similarly, in Rozner v. Bellevue, 116 Wn.2d 342, 804 P.2d 24 (1991), the issue was municipal liability."
    
    try:
        # Test direct processing (async)
        import asyncio
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        async def run_test():
            processor = UnifiedCitationProcessorV2()
            result = await processor.process_text(test_text)
            
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations")
            
            for cit in citations:
                citation_text = cit.citation
                extracted_name = cit.extracted_case_name
                
                print(f"\n🔍 {citation_text}:")
                print(f"   Extracted: '{extracted_name}'")
                
                # Check if improvements were applied
                if "Department of Ecology" in extracted_name:
                    print(f"   ✅ Abbreviation expansion WORKED")
                elif "Dep't of Ecology" in extracted_name:
                    print(f"   ❌ Abbreviation expansion NOT applied")
                
                if "City of Bellevue" in extracted_name:
                    print(f"   ✅ Missing words detection WORKED")
                elif "v. Bellevue" in extracted_name:
                    print(f"   ❌ Missing words detection NOT applied")
        
        # Run the async test
        asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improvements_debug()
