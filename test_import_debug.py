#!/usr/bin/env python3
"""
Test to check if the import is working correctly
"""

def test_import():
    """Test if the import works"""
    
    print("🔍 Testing import...")
    
    try:
        from src.app_final_vue import verify_citation_with_extraction
        print("✅ Import successful!")
        
        # Test the function
        result = verify_citation_with_extraction(
            citation_text="534 F.3d 1290",
            document_text="Punx v Smithers, 534 F.3d 1290 (1921)"
        )
        
        print("✅ Function call successful!")
        print(f"Result: {result}")
        print(f"extracted_case_name: '{result.get('extracted_case_name')}'")
        print(f"extracted_date: '{result.get('extracted_date')}'")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ Function call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_import() 