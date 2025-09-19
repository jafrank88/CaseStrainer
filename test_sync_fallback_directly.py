#!/usr/bin/env python3
"""
Test the sync fallback directly by calling the UnifiedInputProcessor.
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_sync_fallback_directly():
    """Test the sync fallback by calling UnifiedInputProcessor directly."""
    
    try:
        from src.unified_input_processor import process_text_input
        import uuid
        
        # Create a large document with known citations
        base_text = """
        Legal Document Test
        
        Important cases:
        1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
        2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
        3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
        """
        
        # Make it large enough to trigger async processing
        large_text = base_text + "\n\nAdditional content. " * 1000
        
        print("🧪 Testing UnifiedInputProcessor Directly")
        print("=" * 50)
        print(f"📄 Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
        print()
        
        print("📤 Processing with process_text_input...")
        request_id = str(uuid.uuid4())
        result = process_text_input(large_text, request_id)
        
        print(f"📊 Processing result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        print(f"  Processing mode: {result.get('metadata', {}).get('processing_mode')}")
        
        citations = result.get('citations', [])
        if len(citations) > 0:
            print(f"  📋 Sample citations:")
            for i, citation in enumerate(citations[:3]):
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', 'N/A')
                    case_name = citation.get('extracted_case_name', 'N/A')
                else:
                    citation_text = str(citation)
                    case_name = 'N/A'
                print(f"    {i+1}. {citation_text} - {case_name}")
            return True
        else:
            print(f"  ❌ No citations found")
            
            # Check for errors
            if 'error' in result:
                print(f"  🚨 Error: {result['error']}")
            
            return False
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the direct processor test."""
    success = test_sync_fallback_directly()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Direct processor test")
    return success

if __name__ == "__main__":
    main()
