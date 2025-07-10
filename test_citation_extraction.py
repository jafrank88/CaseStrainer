#!/usr/bin/env python3
"""
Test to see what citations are being extracted from the text
"""

from src.document_processing import enhanced_processor

def test_citation_extraction():
    """Test citation extraction"""
    
    text = "Punx v Smithers, 534 F.3d 1290 (1921)"
    
    print("🔍 Testing citation extraction...")
    print(f"Text: '{text}'")
    print("-" * 60)
    
    try:
        # Test the process_document method
        result = enhanced_processor.process_document(
            content=text,
            extract_case_names=True
        )
        
        print("✅ Process document result:")
        print(f"Success: {result.get('success')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        
        for i, citation in enumerate(result.get('citations', [])):
            print(f"\n📋 Citation {i+1}:")
            print(f"  citation: '{citation.get('citation', 'NOT_FOUND')}'")
            print(f"  extracted_case_name: '{citation.get('extracted_case_name', 'NOT_FOUND')}'")
            print(f"  extracted_date: '{citation.get('extracted_date', 'NOT_FOUND')}'")
            print(f"  case_name: '{citation.get('case_name', 'NOT_FOUND')}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_extraction() 