#!/usr/bin/env python3
"""
Test the extraction function directly to see what it returns
"""

from src.case_name_extraction_core import extract_case_name_triple

def test_direct_extraction():
    """Test the extraction function directly"""
    
    text = "Punx v Smithers, 534 F.3d 1290 (1921)"
    citation = "534 F.3d 1290"
    
    print("🔍 Testing direct extraction...")
    print(f"Text: '{text}'")
    print(f"Citation: '{citation}'")
    print("-" * 60)
    
    try:
        result = extract_case_name_triple(
            text=text,
            citation=citation,
            context_window=200
        )
        
        print("✅ Extraction Result:")
        print(f"Type: {type(result)}")
        if result:
            print(f"Keys: {list(result.keys())}")
            for key, value in result.items():
                print(f"  {key}: '{value}'")
        else:
            print("Result is None/False")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_extraction() 