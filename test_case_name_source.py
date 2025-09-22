#!/usr/bin/env python3

def test_case_name_source():
    """Test to identify where case_name is being added to citation objects."""
    
    print("🔍 CASE_NAME SOURCE INVESTIGATION")
    print("=" * 50)
    
    try:
        from src.models import CitationResult
        
        # Create a basic citation result
        citation = CitationResult(
            citation="192 Wash.2d 453",
            extracted_case_name="Test Case Name",
            canonical_name="Canonical Test Case"
        )
        
        print("📊 INITIAL CITATION OBJECT:")
        print(f"   Type: {type(citation)}")
        print(f"   Has __dict__: {hasattr(citation, '__dict__')}")
        print(f"   Has case_name attr: {hasattr(citation, 'case_name')}")
        
        if hasattr(citation, '__dict__'):
            print(f"   __dict__ contents: {citation.__dict__}")
        
        # Test to_dict method
        print(f"\n📊 CITATION.TO_DICT():")
        dict_result = citation.to_dict()
        print(f"   Has case_name in dict: {'case_name' in dict_result}")
        if 'case_name' in dict_result:
            print(f"   case_name value: '{dict_result['case_name']}'")
        
        # Test dict() conversion
        print(f"\n📊 DICT(CITATION):")
        try:
            direct_dict = dict(citation)
            print(f"   Dict conversion successful")
            print(f"   Has case_name in dict: {'case_name' in direct_dict}")
            if 'case_name' in direct_dict:
                print(f"   case_name value: '{direct_dict['case_name']}'")
        except Exception as e:
            print(f"   Dict conversion failed: {e}")
        
        # Test adding case_name attribute
        print(f"\n📊 ADDING CASE_NAME ATTRIBUTE:")
        citation.case_name = "Dynamically Added Name"
        print(f"   Added case_name attribute")
        print(f"   Has case_name attr: {hasattr(citation, 'case_name')}")
        print(f"   case_name value: {getattr(citation, 'case_name', 'NOT_FOUND')}")
        
        # Test dict conversion after adding attribute
        print(f"\n📊 DICT(CITATION) AFTER ADDING ATTRIBUTE:")
        try:
            direct_dict_after = dict(citation)
            print(f"   Dict conversion successful")
            print(f"   Has case_name in dict: {'case_name' in direct_dict_after}")
            if 'case_name' in direct_dict_after:
                print(f"   case_name value: '{direct_dict_after['case_name']}'")
        except Exception as e:
            print(f"   Dict conversion failed: {e}")
        
        # Test document processing conversion
        print(f"\n📊 DOCUMENT PROCESSING CONVERSION:")
        try:
            from src.document_processing_unified import UnifiedDocumentProcessor
            
            processor = UnifiedDocumentProcessor()
            converted = processor._convert_citation_to_dict(citation)
            
            print(f"   Conversion successful")
            print(f"   Has case_name in result: {'case_name' in converted}")
            if 'case_name' in converted:
                print(f"   case_name value: '{converted['case_name']}'")
            
        except Exception as e:
            print(f"   Document processing conversion failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case_name_source()
